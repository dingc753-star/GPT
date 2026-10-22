#!/usr/bin/env python3
"""images/ 폴더의 이미지를 카드 그리드로 보여주는 gallery.html 생성."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "images"
OUTPUT = ROOT / "gallery.html"

PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>현실 직업 RPG 도감</title>
<style>
  :root {{ --bg:#0f1220; --card:#1a1f35; --text:#e8ebf7; --muted:#9aa3c7; --accent:#7cc4ff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:24px 16px; background:var(--bg); color:var(--text);
         font-family:system-ui,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif; }}
  h1 {{ text-align:center; margin:0 0 4px; }}
  p.sub {{ text-align:center; color:var(--muted); margin:0 0 24px; }}
  .grid {{ display:grid; gap:16px; grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
          max-width:1400px; margin:0 auto; }}
  .card {{ background:var(--card); border-radius:14px; overflow:hidden;
          box-shadow:0 6px 18px rgba(0,0,0,.35); transition:transform .15s; }}
  .card:hover {{ transform:translateY(-4px); }}
  .card img {{ display:block; width:100%; aspect-ratio:2/3; object-fit:cover; background:#000; }}
  .info {{ padding:10px 12px 14px; }}
  .no {{ color:var(--accent); font-weight:700; font-size:.85rem; }}
  .title {{ font-weight:700; margin:2px 0; }}
  .meta {{ color:var(--muted); font-size:.85rem; }}
</style>
</head>
<body>
<h1>현실 직업 RPG 도감</h1>
<p class="sub">{count}명 수록</p>
<div class="grid">
{cards}
</div>
</body>
</html>
"""

CARD = """  <a class="card" href="{src}" target="_blank" style="color:inherit;text-decoration:none">
    <img src="{src}" alt="{alt}" loading="lazy">
    <div class="info">
      <div class="no">No.{no}</div>
      <div class="title">{title}</div>
      <div class="meta">{meta}</div>
    </div>
  </a>"""


def load_meta():
    try:
        with open(ROOT / "characters.json", encoding="utf-8") as f:
            return {c["id"]: c for c in json.load(f)}
    except (OSError, ValueError):
        return {}


def main():
    meta = load_meta()
    images = sorted(p for p in IMAGES_DIR.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}) \
        if IMAGES_DIR.is_dir() else []

    cards = []
    for p in images:
        prefix = p.stem.split("_", 1)[0]
        char = meta.get(int(prefix)) if prefix.isdigit() else None
        title = char["title"] if char else p.stem
        sub = f"{char['class']} · {char['job']}" if char else ""
        cards.append(CARD.format(
            src=html.escape(f"images/{p.name}"),
            alt=html.escape(title),
            no=html.escape(prefix),
            title=html.escape(title),
            meta=html.escape(sub),
        ))

    OUTPUT.write_text(PAGE.format(count=len(cards), cards="\n".join(cards)), encoding="utf-8")
    print(f"{OUTPUT.name} 생성 완료 ({len(cards)}장)")


if __name__ == "__main__":
    main()
