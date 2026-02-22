#!/usr/bin/env python3
"""Generate a Hugo reading markdown file from a GitHub Issue form payload."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

FIELD_MAP = {
    "開催日": "date",
    "文責": "presenter",
    "ステータス": "status",
    "論文タイトル": "paper_title",
    "引用情報": "citation",
    "要点": "key_points",
    "リフレクション": "reflection",
    "タグ": "tags",
}

RE_HEADING = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
NO_RESPONSE = "_No response_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", required=True, help="Path to GITHUB_EVENT_PATH json")
    parser.add_argument(
        "--output-dir",
        default="content/ja/reading",
        help="Primary markdown output directory",
    )
    parser.add_argument(
        "--mirror-dir",
        default="content/japanese/reading",
        help="Optional mirror output directory for current Hugo contentDir",
    )
    return parser.parse_args()


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_issue_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def parse_issue_sections(body: str) -> Dict[str, str]:
    body = normalize_newlines(body)
    matches = list(RE_HEADING.finditer(body))
    result: Dict[str, str] = {}
    if not matches:
        return result

    for idx, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        raw_value = body[start:end].strip()
        value = strip_issue_comments(raw_value).strip()
        if value == NO_RESPONSE:
            value = ""
        result[heading] = value
    return result


def normalize_date(raw: str) -> str:
    value = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return dt.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass

    match = re.search(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", value)
    if match:
        year, month, day = map(int, match.groups())
        return dt.date(year, month, day).isoformat()

    raise ValueError(f"開催日の形式を解釈できません: {raw!r}")


def normalize_tags(raw: str) -> List[str]:
    if not raw:
        return []
    tags: List[str] = []
    seen = set()
    for token in re.split(r"[,、\n]+", raw):
        tag = token.strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def clean_text(text: str) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    value = value.strip(" \"'“”‘’「」[]()")
    return value.rstrip(".")


def extract_title_from_citation(citation: str) -> str:
    compact = " ".join(line.strip() for line in citation.splitlines() if line.strip())
    if not compact:
        return ""

    patterns = [
        r"「([^」]{4,220})」",
        r"“([^”]{4,220})”",
        r"\"([^\"]{4,220})\"",
        r"\(\d{4}[a-z]?\)\.\s*([^\.]{4,220})\.",
        r"\b(?:19|20)\d{2}\.\s*([^\.]{4,220})\.",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact)
        if match:
            candidate = clean_text(match.group(1))
            if candidate:
                return candidate[:160]

    segments = [clean_text(seg) for seg in re.split(r"[。\.]", compact) if clean_text(seg)]
    if not segments:
        return ""

    ranked = sorted(segments, key=len, reverse=True)
    for segment in ranked:
        if len(segment) < 8:
            continue
        if re.search(r"\b(?:19|20)\d{2}\b", segment):
            continue
        if re.search(r"\bet al\b", segment, re.IGNORECASE):
            continue
        return segment[:160]
    return ranked[0][:160]


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:80].strip("-")


def derive_slug(citation: str, title: str, issue_number: int) -> str:
    if title:
        candidate = slugify(title)
        if len(candidate) >= 4:
            return candidate

    for line in citation.splitlines():
        if line.strip():
            candidate = slugify(line.strip())
            if len(candidate) >= 4:
                return candidate

    return f"issue-{issue_number}"


def normalize_points(raw: str) -> List[str]:
    lines = [line.strip() for line in normalize_newlines(raw).splitlines() if line.strip()]
    if not lines:
        return ["- （未記入）"]

    bullets: List[str] = []
    for line in lines:
        if re.match(r"^[-*+]\s+", line):
            text = re.sub(r"^[-*+]\s+", "", line)
            bullets.append(f"- {text}")
            continue
        if re.match(r"^\d+[.)]\s+", line):
            text = re.sub(r"^\d+[.)]\s+", "", line)
            bullets.append(f"- {text}")
            continue
        bullets.append(f"- {line}")
    return bullets


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def indent_block(value: str, indent: int = 2) -> str:
    pad = " " * indent
    lines = normalize_newlines(value).splitlines()
    if not lines:
        return f"{pad}"
    return "\n".join(f"{pad}{line}" if line else pad for line in lines)


def find_existing_issue_file(directory: Path, issue_number: int) -> Optional[Path]:
    if not directory.exists():
        return None
    pattern = re.compile(rf"(?m)^source_issue:\s*{issue_number}\s*$")
    for path in sorted(directory.glob("*.md")):
        if path.name == "_index.md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if pattern.search(text):
            return path
    return None


def build_markdown(
    title: str,
    reading_date: str,
    presenter: str,
    citation: str,
    tags: List[str],
    status: str,
    issue_number: int,
    issue_url: str,
    key_points: List[str],
    reflection: str,
) -> str:
    lines: List[str] = [
        "---",
        f"title: {quote_yaml(title)}",
        f"date: {reading_date}",
        f"presenter: {quote_yaml(presenter)}",
        "citation: |",
        indent_block(citation if citation else "（未記入）"),
    ]

    if tags:
        lines.append("tags:")
        lines.extend(f"  - {quote_yaml(tag)}" for tag in tags)
    else:
        lines.append("tags: []")

    lines.extend(
        [
            f"status: {status}",
            f"source_issue: {issue_number}",
            f"source_issue_url: {quote_yaml(issue_url)}",
            "---",
            "",
            "## 要点（箇条書き）",
            "",
            *key_points,
            "",
            "## リフレクション（任意：議論・出た意見の整理）",
            "",
            reflection.strip() if reflection.strip() else "（未記入）",
            "",
        ]
    )
    return "\n".join(lines)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_required(fields: Dict[str, str], labels: List[str]) -> None:
    missing = [label for label in labels if not fields.get(label, "").strip()]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Issue本文に必須項目がありません: {joined}")


def main() -> int:
    args = parse_args()
    event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))

    issue = event.get("issue", {})
    issue_number = int(issue.get("number"))
    issue_body = issue.get("body") or ""
    issue_url = issue.get("html_url") or ""
    if not issue_url:
        repo = event.get("repository", {})
        full_name = repo.get("full_name", "")
        issue_url = f"https://github.com/{full_name}/issues/{issue_number}"

    sections = parse_issue_sections(issue_body)
    fields = {key: sections.get(label, "") for label, key in FIELD_MAP.items()}
    validate_required(sections, ["開催日", "文責", "引用情報", "要点"])

    reading_date = normalize_date(fields["date"])
    presenter = fields["presenter"].strip()
    raw_status = fields.get("status", "").strip().lower()
    status = raw_status if raw_status in {"done", "upcoming"} else "done"
    paper_title = fields.get("paper_title", "").strip()
    citation = normalize_newlines(fields["citation"]).strip()
    key_points = normalize_points(fields["key_points"])
    reflection = normalize_newlines(fields["reflection"]).strip()
    tags = normalize_tags(fields["tags"])

    extracted_title = extract_title_from_citation(citation)
    title = paper_title if paper_title else extracted_title if extracted_title else f"Reading #{reading_date}"
    slug_source_title = paper_title if paper_title else extracted_title
    slug = derive_slug(citation, slug_source_title, issue_number)

    output_dir = Path(args.output_dir)
    mirror_dir = Path(args.mirror_dir) if args.mirror_dir else None
    filename = f"{reading_date}-{slug}.md"

    existing_primary = find_existing_issue_file(output_dir, issue_number)
    primary_path = existing_primary if existing_primary else output_dir / filename

    markdown = build_markdown(
        title=title,
        reading_date=reading_date,
        presenter=presenter,
        citation=citation,
        tags=tags,
        status=status,
        issue_number=issue_number,
        issue_url=issue_url,
        key_points=key_points,
        reflection=reflection,
    )

    write_file(primary_path, markdown)

    if mirror_dir:
        if str(mirror_dir.resolve()) != str(output_dir.resolve()):
            existing_mirror = find_existing_issue_file(mirror_dir, issue_number)
            mirror_path = mirror_dir / primary_path.name
            if existing_mirror and existing_mirror != mirror_path and existing_mirror.exists():
                existing_mirror.unlink()
            write_file(mirror_path, markdown)

    print(f"generated_file={primary_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
