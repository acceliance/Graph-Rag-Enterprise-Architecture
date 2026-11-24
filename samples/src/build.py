"""Build the sample PDFs of ../source-docs from the Markdown sources of this folder.

Each *.md file becomes one PDF: fenced ``context`` blocks are drawn as an SVG context
diagram, pandoc turns the Markdown into HTML, and a headless Chromium browser (Microsoft
Edge or Google Chrome) prints the HTML to PDF.

Usage:  python build.py
Needs:  pandoc on the PATH, and Edge or Chrome installed.
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "source-docs"
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "microsoft-edge", "google-chrome", "chromium", "chromium-browser",
]


def find_browser() -> str:
    for candidate in BROWSERS:
        found = candidate if Path(candidate).is_file() else shutil.which(candidate)
        if found:
            return str(found)
    sys.exit("No Edge, Chrome or Chromium found: cannot print the PDFs.")


def context_svg(spec: str) -> str:
    """Draw a central system with its satellites on both sides, one labelled link each."""
    center, caption, sides = "", "", {"left": [], "right": []}
    for line in spec.strip().splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key == "center":
            center = value
        elif key == "caption":
            caption = value
        elif key in sides:
            name, _, label = value.partition("|")
            sides[key].append((name.strip(), label.strip()))

    rows = max(len(sides["left"]), len(sides["right"]))
    box_w, box_h, gap, width, run = 240, 34, 12, 1000, 160
    height = rows * (box_h + gap) + gap
    cx, cw = (width - 200) / 2, 200
    esc = html.escape
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{esc(caption)}">'
    ]
    for side, items in sides.items():
        offset = (rows - len(items)) * (box_h + gap) / 2
        for i, (name, label) in enumerate(items):
            y = gap + offset + i * (box_h + gap)
            mid = y + box_h / 2
            # The link leaves the box horizontally (the label sits on that part), then
            # goes to the central box.
            if side == "left":
                x, x1, x2, x3 = 0, box_w, box_w + run, cx
            else:
                x, x1, x2, x3 = width - box_w, width - box_w, width - box_w - run, cx + cw
            ty = height / 2 + (mid - height / 2) * 0.12
            out.append(f'<polyline class="link" points="{x1},{mid} {x2},{mid} {x3},{ty}"/>')
            out.append(f'<text class="label" x="{(x1 + x2) / 2}" y="{mid - 4}" text-anchor="middle">{esc(label)}</text>')
            out.append(f'<rect class="sat" x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="4"/>')
            out.append(f'<text class="name" x="{x + box_w / 2}" y="{mid + 4}" text-anchor="middle">{esc(name)}</text>')
    out.append(f'<rect class="core" x="{cx}" y="{height / 2 - 45}" width="{cw}" height="90" rx="6"/>')
    words, lines, current = center.split(), [], ""
    for word in words:
        if len(current) + len(word) > 16 and current:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    lines.append(current)
    for i, text in enumerate(lines):
        y = height / 2 + 5 + (i - (len(lines) - 1) / 2) * 18
        out.append(f'<text class="corename" x="{width / 2}" y="{y}" text-anchor="middle">{esc(text)}</text>')
    out.append("</svg>")
    return f'<figure>\n{"".join(out)}\n<figcaption>{esc(caption)}</figcaption>\n</figure>'


def build(md: Path, browser: str, tmp: Path) -> Path:
    text = md.read_text(encoding="utf-8")
    text = re.sub(r"```context\n(.*?)```", lambda m: context_svg(m.group(1)), text, flags=re.S)
    source = tmp / md.name
    source.write_text(text, encoding="utf-8")
    page = tmp / (md.stem + ".html")
    subprocess.run(
        ["pandoc", str(source), "--from", "markdown+pipe_tables-implicit_figures", "--to", "html5",
         "--standalone", "--embed-resources", "--css", str(HERE / "style.css"),
         "--template", str(HERE / "template.html"), "--output", str(page)],
        check=True,
    )
    pdf = OUT / (md.stem + ".pdf")
    pdf.unlink(missing_ok=True)
    # One browser profile per document: with a shared profile the second launch hands over
    # to the first process and returns before anything is printed.
    subprocess.run(
        [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--user-data-dir={tmp / ('profile-' + md.stem)}", f"--print-to-pdf={pdf}", page.as_uri()],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        if pdf.is_file() and pdf.stat().st_size > 0:
            return pdf
        time.sleep(0.2)
    sys.exit(f"The browser did not write {pdf.name}.")


def main() -> None:
    browser = find_browser()
    OUT.mkdir(exist_ok=True)
    # The browser may still hold its profile lock for a moment after printing (Windows).
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        for md in sorted(HERE.glob("*.md")):
            print("built", build(md, browser, Path(folder)).name)


if __name__ == "__main__":
    main()
