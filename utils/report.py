from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from utils.models import ProgramRecord


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def write_programs_markdown(records: list[ProgramRecord], output_path: str) -> None:
    dated: dict[str, list[ProgramRecord]] = defaultdict(list)

    for record in records:
        date_key = record.launched_at.strftime("%Y-%m-%d") if record.launched_at else "unknown"
        dated[date_key].append(record)

    def date_sort_key(item: tuple[str, list[ProgramRecord]]):
        key, _ = item
        if key == "unknown":
            return datetime.min
        return datetime.strptime(key, "%Y-%m-%d")

    lines = ["# programs", ""]

    for date_key, date_records in sorted(dated.items(), key=date_sort_key, reverse=True):
        lines.append(f"## {date_key}")
        lines.append("")

        date_records_sorted = sorted(
            date_records,
            key=lambda r: (r.launched_at or datetime.min, r.name.lower()),
            reverse=True,
        )

        for record in date_records_sorted:
            lines.append(f"### {record.name} ({record.platform})")
            lines.append("")

            lines.append("#### wildcards")
            wildcards = _dedupe_keep_order(record.wildcards)
            if wildcards:
                for wildcard in wildcards:
                    lines.append(f"- {wildcard}")
            else:
                lines.append("- none")
            lines.append("")

            lines.append("#### domains")
            domains = _dedupe_keep_order(record.domains)
            if domains:
                for domain in domains:
                    lines.append(f"- {domain}")
            else:
                lines.append("- none")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines).rstrip() + "\n")
