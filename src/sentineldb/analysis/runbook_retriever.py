"""
Runbook retriever — keyword-based markdown runbook search.

Scores each runbook by keyword overlap between the alert type name +
evidence labels and the runbook's content. Returns the top match above
a relevance threshold, or None if no match clears the threshold.
"""

from __future__ import annotations

import re
from pathlib import Path

from sentineldb.core.enums import AlertType
from sentineldb.core.models import RunbookMatch

_THRESHOLD = 0.2
_RUNBOOKS_DIR = Path(__file__).parent.parent.parent.parent / "runbooks"


def _tokenise(text: str) -> set[str]:
    """Lower-case word tokens, stripping punctuation and underscores."""
    # Replace underscores with spaces so 'cpu_high' -> 'cpu', 'high'
    text = text.replace("_", " ")
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _score(title_tokens: set[str], content_tokens: set[str], query_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    # Core score is fraction of query tokens present in the document
    overlap = content_tokens & query_tokens
    score = len(overlap) / len(query_tokens)

    # Bonus for query tokens appearing in the title
    title_overlap = title_tokens & query_tokens
    if title_overlap:
        score += (len(title_overlap) / len(query_tokens)) * 0.5

    return score


class RunbookRetriever:
    """Keyword-based runbook search over local markdown files."""

    def __init__(self, runbooks_dir: str | Path = _RUNBOOKS_DIR) -> None:
        self._dir = Path(runbooks_dir)
        self._runbooks: list[tuple[Path, str, str]] = []  # (path, title, content)
        self._load()

    def _load(self) -> None:
        if not self._dir.exists():
            return
        for path in sorted(self._dir.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            # First H1 heading is the title
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else path.stem
            self._runbooks.append((path, title, content))

    def find_match(
        self,
        alert_type: AlertType,
        evidence_labels: list[str],
    ) -> RunbookMatch | None:
        if not self._runbooks:
            return None

        # Build query token set from alert type name + evidence labels
        query_tokens = _tokenise(alert_type.value) | {
            tok for label in evidence_labels for tok in _tokenise(label)
        }

        best_score = 0.0
        best: tuple[Path, str, str] | None = None

        for path, title, content in self._runbooks:
            title_tokens = _tokenise(title)
            content_tokens = _tokenise(content)
            score = _score(title_tokens, content_tokens, query_tokens)
            if score > best_score:
                best_score = score
                best = (path, title, content)

        if best is None or best_score < _THRESHOLD:
            return None

        path, title, content = best
        snippet = _extract_snippet_text(content, query_tokens)

        return RunbookMatch(
            path=str(path.relative_to(Path.cwd()) if path.is_absolute() else path),
            title=title,
            relevant_snippet=snippet,
            score=best_score,
        )


def _extract_snippet_text(content: str, keywords: set[str]) -> str:
    """Return the first paragraph that overlaps with keywords (as raw text)."""
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    for para in paragraphs:
        if _tokenise(para) & keywords:
            return para[:400]
    return paragraphs[0][:400] if paragraphs else ""
