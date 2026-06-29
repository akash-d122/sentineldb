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
from sentineldb.core.models import AlertPayload, IncidentReport
from sentineldb.db.models import IncidentORM, IncidentReportORM
from sentineldb.db.session import AsyncSessionLocal
from sentineldb.llm.summarizer import LLMSummarizer
from sentineldb.registry.loader import InstanceRegistry
from sentineldb.worker.app import celery_app

logger = logging.getLogger(__name__)

# Registry is loaded once per worker process
_registry = InstanceRegistry()
_retriever = RunbookRetriever()
_analyzer = Analyzer()
_renderer = Renderer()
_summarizer = LLMSummarizer()


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
        return report.report_id
    except Exception as e:
        logger.exception("Task failed for incident %s: %s", incident_id, e)
        # Update incident status to failed
        asyncio.run(_mark_failed(incident_id))
        raise self.retry(exc=e, countdown=10)


async def _analyze(incident_id: str, alert: AlertPayload) -> IncidentReport:
    """Async core pipeline execution."""
    # 1. Resolve instance
    instance = _registry.resolve(alert.instance_id)

    # 2. Collect evidence
    # Currently only PostgreSQL is implemented
    if instance.engine == "postgresql":
        collector = PostgresCollector(instance)
    else:
        raise NotImplementedError(f"Collector for engine {instance.engine} not implemented.")

    bundle = await collector.collect()

    # 3. Analyze
    causes = _analyzer.rank_causes(bundle)
    top_cause = causes[0]

    # 4. Runbook Retrieval
    labels = [item.label for item in bundle.items if item.value is not None]
    runbook = _retriever.find_match(alert.alert_type, labels)

    # 5. Render Output
    report = _renderer.render(alert, top_cause, bundle, runbook)

    # 6. Optional LLM Polish
    # Generate a string summary of evidence for the LLM
    evidence_lines = [f"- {i.display_text}" for i in bundle.items]
    evidence_text = "\n".join(evidence_lines)

    polished_summary = _summarizer.summarize(top_cause, evidence_text)
    if polished_summary:
        # Pydantic v2 immutable copy with updates
        report = report.model_copy(update={
            "root_cause_summary": polished_summary,
            "llm_used": True,
        })

    # 7. Persist to DB
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"prepared_statement_cache_size": 0},
        echo=False,
    )
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) # type: ignore

    async with LocalSession() as session:
        # Update incident status
        incident = await session.get(IncidentORM, incident_id)
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
            runbook_reference=report.runbook_reference.model_dump(mode="json") if report.runbook_reference else None,
            safe_next_actions=[a.model_dump(mode="json") for a in report.safe_next_actions],
            requires_approval=report.requires_approval,
            missing_evidence=report.missing_evidence,
            llm_used=report.llm_used,
            generated_at=report.generated_at,
        )
        session.add(db_report)
        await session.commit()

    await engine.dispose()
    return report


async def _mark_failed(incident_id: str) -> None:
    """Update the incident row to failed status."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"prepared_statement_cache_size": 0},
        echo=False,
    )
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) # type: ignore

    async with LocalSession() as session:
        incident = await session.get(IncidentORM, incident_id)
        if incident:
            incident.status = "failed"
            await session.commit()
    await engine.dispose()
