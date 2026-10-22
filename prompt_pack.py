#!/usr/bin/env python3
"""ChatGPT 웹(브라우저)에 붙여넣을 프롬프트 모음 prompts.html 생성.

캐릭터별 카드에 [복사] 버튼이 있어, ChatGPT 채팅창에 하나씩 붙여넣고
결과 이미지를 다운로드한 뒤 import_images.py로 정리하면 됩니다.
"""

import argparse
import html
from pathlib import Path

from generate import REFERENCE_INSTRUCTION, ROOT, build_prompt, load_characters, load_style, output_path

OUTPUT = ROOT / "prompts.html"

PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RPG 도감 프롬프트</title>
<style>
  :root {{ --bg:#0f1220; --card:#1a1f35; --text:#e8ebf7; --muted:#9aa3c7; --accent:#7cc4ff; --ok:#5fd38d; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:24px 16px; background:var(--bg); color:var(--text);
         font-family:system-ui,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif; }}
  main {{ max-width:900px; margin:0 auto; }}
  h1 {{ margin:0 0 8px; }}
  .guide {{ color:var(--muted); line-height:1.6; margin-bottom:20px; }}
  .card {{ background:var(--card); border-radius:12px; padding:14px 16px; margin-bottom:14px; }}
  .card.done {{ opacity:.45; }}
  .head {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; }}
  .no {{ color:var(--accent); font-weight:700; }}
  .file {{ color:var(--muted); font-size:.85rem; margin-left:auto; }}
  pre {{ white-space:pre-wrap; word-break:break-word; background:#0b0e19; padding:10px; border-radius:8px;
        font-size:.85rem; margin:10px 0; }}
  button {{ background:var(--accent); color:#0b0e19; border:0; border-radius:8px; padding:6px 14px;
           font-weight:700; cursor:pointer; }}
  button.copied {{ background:var(--ok); }}
  label {{ color:var(--muted); font-size:.85rem; margin-left:10px; }}
</style>
</head>
<body>
<main>
<h1>RPG 도감 프롬프트 ({count}개)</h1>
<div class="guide">
1. chatgpt.com에 로그인 → 새 채팅<br>
2. [복사] → 채팅창에 붙여넣기 → 생성된 이미지 다운로드<br>
3. 다 받은 뒤 <code>python import_images.py ~/Downloads</code> 로 images/에 번호대로 정리<br>
※ 다운로드는 반드시 번호 순서대로 하세요. 체크 표시는 이 브라우저에만 저장됩니다.
</div>
{cards}
</main>
<script>
  function key(id) {{ return "rpg-done-" + id; }}
  document.querySelectorAll(".card").forEach(function (card) {{
    var id = card.dataset.id, box = card.querySelector("input");
    try {{ box.checked = localStorage.getItem(key(id)) === "1"; }} catch (e) {{}}
    card.classList.toggle("done", box.checked);
    box.addEventListener("change", function () {{
      card.classList.toggle("done", box.checked);
      try {{ localStorage.setItem(key(id), box.checked ? "1" : "0"); }} catch (e) {{}}
    }});
    card.querySelector("button").addEventListener("click", function () {{
      var btn = this, text = card.querySelector("pre").innerText;
      navigator.clipboard.writeText(text).then(function () {{
        btn.textContent = "복사됨"; btn.classList.add("copied");
        setTimeout(function () {{ btn.textContent = "복사"; btn.classList.remove("copied"); }}, 1500);
      }});
    }});
  }});
</script>
</body>
</html>
"""

CARD = """<div class="card" data-id="{id}">
  <div class="head">
    <span class="no">No.{no}</span><strong>{title}</strong>
    <button type="button">복사</button>
    <label><input type="checkbox"> 완료</label>
    <span class="file">{file}</span>
  </div>
  <pre>{prompt}</pre>
</div>"""

# ChatGPT 웹은 크기 파라미터가 없으므로 문장으로 요청
WEB_PREFIX = "Generate one image, portrait 2:3 aspect ratio.\n"

# 한 채팅방에서 "다음"만 입력하며 순서대로 진행하는 세션 메시지
SESSION_HEAD = (
    "We will create a series of {count} character card illustrations, one image per turn, in the order below.\n"
    "Rules: portrait 2:3 aspect ratio, keep the exact same art style across the whole series, "
    "one image per reply, no text in the reply other than the number.\n"
    "Common style: {style}\n"
    "{reference}Generate #{first} now. Each time I reply \"next\", generate the next one in the list.\n"
)


def main():
    p = argparse.ArgumentParser(description="ChatGPT 웹용 프롬프트 모음(prompts.html) 생성")
    p.add_argument("--only", type=int, nargs="+", metavar="ID", help="지정한 번호만 포함")
    p.add_argument("--reference", action="store_true",
                   help="기준 이미지를 채팅에 첨부해서 쓸 때: 화풍 참고 지시문 포함")
    args = p.parse_args()

    style = load_style()
    chars = load_characters()
    if args.only:
        chars = [c for c in chars if c["id"] in set(args.only)]

    cards = [CARD.format(
        id=c["id"], no=f"{c['id']:02d}", title=html.escape(c["title"]),
        file=html.escape(output_path(c).name),
        prompt=html.escape(WEB_PREFIX + build_prompt(c, style, args.reference)),
    ) for c in chars]

    session = SESSION_HEAD.format(count=len(chars), style=style,
                                   reference=REFERENCE_INSTRUCTION + "\n" if args.reference else "", first=f"{chars[0]['id']:02d}") if chars else ""
    for c in chars:
        body = build_prompt(c, "").strip()
        session += f"\n#{c['id']:02d}\n{body}\n"
    cards.insert(0, CARD.format(
        id="all", no="ALL", title="한 채팅방에서 순서대로 진행 (권장)",
        file="이걸 붙여넣고 이후엔 &quot;next&quot;만 입력",
        prompt=html.escape(session),
    ))

    OUTPUT.write_text(PAGE.format(count=len(chars), cards="\n".join(cards)), encoding="utf-8")
    print(f"{OUTPUT.name} 생성 완료 ({len(chars)}개 + 일괄 진행 메시지) - 브라우저로 열어서 사용하세요")


if __name__ == "__main__":
    main()
