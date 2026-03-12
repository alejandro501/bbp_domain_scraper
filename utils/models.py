from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QueryOptions:
    mode: str = "all"  # all|new
    cutoff: datetime | None = None
    interval_label: str = "all"


@dataclass
class ProgramRecord:
    platform: str
    name: str
    launched_at: datetime | None
    wildcards: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
