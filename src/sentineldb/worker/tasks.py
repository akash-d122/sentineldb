"""
Celery background tasks for incident analysis.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine

from sentineldb.analysis.renderer import Renderer
from sentineldb.analysis.rules import Analyzer
from sentineldb.analysis.runbook_retriever import RunbookRetriever
from sentineldb.collectors.postgres import PostgresCollector
from sentineldb.core.config import settings
from sentineldb.core.models import AlertPayload, EvidenceBundle, IncidentReport
from sentineldb.db.models import IncidentORM, IncidentReportORM
from sentineldb.llm.summarizer import LLMSummarizer
from sentineldb.notifications.dispatcher import NotificationDispatcher
from sentineldb.registry.loader import InstanceRegistry
from sentineldb.worker.app import celery_app

logger = logging.getLogger(__name__)

# Registry is loaded once per worker process
_registry = InstanceRegistry()
_retriever = RunbookRetriever()
_analyzer = Analyzer()
_renderer = Renderer()
_summarizer = LLMSummarizer()
_dispatcher = NotificationDispatcher()


@celery_app.task(bind=True, max_retries=3)
def dispatch_notifications(self: Any, incident_id: str) -> None:
    """Task to dispatch notifications asynchronously."""
    logger.info("Starting notification dispatch for incident %s", incident_id)
    try:
        asyncio.run(_dispatch_notifications_async(incident_id))
    except Exception as e:
        logger.exception("Failed to dispatch notifications for incident %s: %s", incident_id, e)
        raise self.retry(exc=e, countdown=10)


async def _dispatch_notifications_async(incident_id: str) -> None:
    import uuid

    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"prepared_statement_cache_size": 0},
        echo=False,
    )
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    try:
        async with LocalSession() as session:
            stmt = select(IncidentReportORM).where(
                IncidentReportORM.incident_id == uuid.UUID(incident_id)
            )
            result = await session.execute(stmt)
            db_report = result.scalar_one_or_none()
    finally:
        await engine.dispose()

    if not db_report:
        logger.error("Could not find report for incident %s to notify", incident_id)
        return

    # Convert back to Pydantic model for dispatcher
    from sentineldb.core.models import IncidentReport

    report = IncidentReport.model_validate(db_report, from_attributes=True)
    await _dispatcher.dispatch(report)


@celery_app.task(bind=True, max_retries=3)
def run_incident_analysis(self: Any, incident_id: str, alert_payload_dict: dict[str, Any]) -> str:
    """
    Run the complete incident analysis pipeline.

    Since Celery workers use prefork (processes) by default, and asyncpg/SQLAlchemy
    need event loops, we run the pipeline in a synchronous wrapper that creates an
    event loop via asyncio.run(). We explicitly manage the SQLAlchemy engine inside
    the task so it isn't shared across different event loops.
    """
    logger.info("Starting analysis for incident %s", incident_id)

    try:
        alert = AlertPayload.model_validate(alert_payload_dict)
        report = asyncio.run(_analyze(incident_id, alert))

        # Enqueue the notifications task
        dispatch_notifications.delay(incident_id)

        return report.report_id
    except Exception as e:
        logger.exception("Task failed for incident %s: %s", incident_id, e)
        # Update incident status to failed
        try:
            asyncio.run(_mark_failed(incident_id))
        except Exception as inner_e:
            logger.exception("Failed to mark incident %s as failed: %s", incident_id, inner_e)
        raise self.retry(exc=e, countdown=10)


async def _analyze(incident_id: str, alert: AlertPayload) -> IncidentReport:
    """Async core pipeline execution."""
    import uuid

    # 1. Resolve instance
    instance = _registry.resolve(alert.instance_id)

    # 2. Collect evidence
    if instance.engine == "postgresql":
        collector = PostgresCollector(instance)
    elif instance.engine == "mysql":
        from sentineldb.collectors.mysql import MySQLCollector

        collector = MySQLCollector(instance)
    else:
        raise NotImplementedError(f"Collector for engine {instance.engine} not implemented.")

    bundle = await collector.collect()

    # 2b. Collect external monitoring evidence if configured
    if instance.monitoring and instance.monitoring.provider == "cloudwatch":
        from sentineldb.collectors.cloudwatch import CloudWatchCollector

        cw_collector = CloudWatchCollector(instance)
        cw_bundle = await cw_collector.collect()
        bundle = EvidenceBundle(
            instance_id=bundle.instance_id,
            collected_at=bundle.collected_at,
            items=list(bundle.items) + list(cw_bundle.items),
        )
    elif instance.monitoring and instance.monitoring.provider == "prometheus":
        from sentineldb.collectors.prometheus import PrometheusCollector

        prom_collector = PrometheusCollector(instance)
        prom_bundle = await prom_collector.collect()
        bundle = EvidenceBundle(
            instance_id=bundle.instance_id,
            collected_at=bundle.collected_at,
            items=list(bundle.items) + list(prom_bundle.items),
        )

    # 3. Analyze
    causes = _analyzer.rank_causes(bundle)
    top_cause = causes[0]

    # 4. Runbook Retrieval
    labels = [item.label for item in bundle.items if item.value is not None]
    runbook = _retriever.find_match(alert.alert_type, labels)

    # 5. Render Output
    report = _renderer.render(incident_id, alert, top_cause, bundle, runbook)

    # 6. Optional LLM Polish
    # Generate a string summary of evidence for the LLM
    evidence_lines = [f"- {i.display_text}" for i in bundle.items]
    evidence_text = "\n".join(evidence_lines)

    polished_summary = _summarizer.summarize(top_cause, evidence_text)
    if polished_summary:
        # Pydantic v2 immutable copy with updates
        report = report.model_copy(
            update={
                "root_cause_summary": polished_summary,
                "llm_used": True,
            }
        )

    # 7. Persist to DB
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"prepared_statement_cache_size": 0},
        echo=False,
    )
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    try:
        async with LocalSession() as session:
            # Update incident status
            incident = await session.get(IncidentORM, uuid.UUID(incident_id))
            if incident:
                incident.status = "report_ready"

            # Save report
            db_report = IncidentReportORM(
                report_id=report.report_id,
                incident_id=report.incident_id,
                rca_strength=report.rca_strength.value,
                root_cause_summary=report.root_cause_summary,
                why_most_likely=report.why_most_likely,
                evidence=[i.model_dump(mode="json") for i in report.evidence],
                runbook_reference=report.runbook_reference.model_dump(mode="json")
                if report.runbook_reference
                else None,
                safe_next_actions=[a.model_dump(mode="json") for a in report.safe_next_actions],
                requires_approval=report.requires_approval,
                missing_evidence=report.missing_evidence,
                llm_used=report.llm_used,
                generated_at=report.generated_at,
            )
            session.add(db_report)
            await session.commit()
    finally:
        await engine.dispose()
    return report


async def _mark_failed(incident_id: str) -> None:
    """Update the incident row to failed status."""
    import uuid

    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"prepared_statement_cache_size": 0},
        echo=False,
    )
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    try:
        async with LocalSession() as session:
            incident = await session.get(IncidentORM, uuid.UUID(incident_id))
            if incident:
                incident.status = "failed"
                await session.commit()
    finally:
        await engine.dispose()
