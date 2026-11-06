#!/usr/bin/env python3
"""Render archived Japanese research-audit Markdown files as A4 PDFs."""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "report"
FILENAME = re.compile(r"^(?P<number>\d{4,})_\d{4}-\d{2}-\d{2}(?:_\d{2}-\d{2})?$")
TITLE = re.compile(r"(?m)^#{1,3}\s*(?:0[.．]\s*)?第\s*(\d+)\s*回研究監査")

CSS = r"""
@page {
  size: A4;
  margin: 19mm 18mm 20mm;
  @bottom-right {
    content: counter(page) " / " counter(pages);
    color: #64748b;
    font-size: 8pt;
  }
}
html { background: #fff; }
body {
  font-family: "Noto Sans CJK JP", "Noto Sans", sans-serif;
  font-size: 9.8pt;
  line-height: 1.64;
  color: #1e293b;
  overflow-wrap: anywhere;
}
h1 { font-size: 19pt; line-height: 1.35; color: #0f172a; border-bottom: 2px solid #2563eb; padding-bottom: 5mm; margin: 0 0 7mm; }
h2 { font-size: 13.5pt; color: #1d4ed8; margin-top: 6mm; margin-bottom: 2mm; break-after: avoid; }
h3 { font-size: 11.2pt; color: #334155; margin-top: 4mm; margin-bottom: 1.5mm; break-after: avoid; }
p { margin: 0 0 3mm; }
ul, ol { margin-top: 1mm; margin-bottom: 4mm; padding-left: 7mm; }
li { margin-bottom: 0.8mm; }
strong { color: #0f172a; }
a { color: #1d4ed8; text-decoration: none; }
table { border-collapse: collapse; width: 100%; font-size: 8pt; table-layout: fixed; margin: 4mm 0; }
th, td { border: 1px solid #cbd5e1; padding: 2mm 2.5mm; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { background: #f1f5f9; }
tr { break-inside: avoid; }
blockquote { border-left: 3px solid #94a3b8; padding-left: 4mm; color: #475569; margin: 3mm 0; }
pre, code { font-family: monospace; font-size: 8pt; overflow-wrap: anywhere; white-space: pre-wrap; }
pre { background: #f8fafc; padding: 3mm; border: 1px solid #e2e8f0; }
hr { border: 0; border-top: 1px solid #cbd5e1; margin: 6mm 0; }
"""

def validate(path: Path, source: str) -> int:
    match = FILENAME.fullmatch(path.stem)
    if not match:
        raise ValueError(f"Invalid report filename: {path.name}; expected 0001_YYYY-MM-DD_HH-MM.md")
    number = int(match.group("number"))
    if "研究対象：デジタル利用権" not in source or "現物の機材・図書の貸出管理ではない" not in source:
        raise ValueError(f"{path.name}: required digital-rights scope statement is missing")
    title = TITLE.search(source)
    if title is None or int(title.group(1)) != number:
        raise ValueError(f"{path.name}: report heading number must match filename number ({number})")
    for section in range(1, 11):
        if not re.search(rf"(?m)^#{{1,6}}\s*{section}[.．]\s+", source):
            raise ValueError(f"{path.name}: required section {section} is missing")
    return number

def render(path: Path, force: bool) -> None:
    target = path.with_suffix(".pdf")
    if target.exists() and not force:
        print(f"SKIP existing: {target.relative_to(ROOT)}")
        return
    source = path.read_text(encoding="utf-8")
    number = validate(path, source)
    body = markdown.markdown(source, extensions=["tables", "fenced_code", "sane_lists", "nl2br"])
    content = (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        f'<title>{html.escape("第" + str(number) + "回研究監査")}</title>'
        f'<style>{CSS}</style></head><body>{body}</body></html>'
    )
    HTML(string=content, base_url=str(ROOT)).write_pdf(str(target))
    if not target.is_file() or target.stat().st_size < 1024 or target.read_bytes()[:4] != b"%PDF":
        raise RuntimeError(f"PDF output verification failed for {path.name}")
    print(f"CREATED: {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="Rebuild PDFs that already exist")
    args = ap.parse_args()
    reports = sorted(ARCHIVE.glob("*.md"))
    for path in reports:
        render(path, args.all)
    print(f"Checked {len(reports)} archived Markdown reports")

if __name__ == "__main__":
    main()
