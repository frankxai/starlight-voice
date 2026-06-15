"""Proactive layer — overnight repo/domain analysis -> ranked morning brief.

Plain Python (subprocess git + httpx), NO LangGraph/deepagents — the synthesis confirmed the
MVP needs neither. A scheduled task runs `analyzer` at 04:30; the first push-to-talk of the
day speaks the cached brief through the realtime TTS lane (so it still hits the latency budget).
"""

from .analyzer import RepoFinding, scan_repos, score_findings, build_brief  # noqa: F401
