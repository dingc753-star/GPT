#!/usr/bin/env python3
"""현실 직업 RPG 도감 - 캐릭터 일러스트 순차 생성기.

사용 예:
    python generate.py --dry-run              # 프롬프트만 출력
    python generate.py                        # 없는 이미지만 순서대로 생성
    python generate.py --only 1 2             # 1, 2번만 (덮어쓰기) 재생성
    python generate.py --reference ref.png    # 기준 이미지를 화풍 참고로 사용
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHARACTERS_FILE = ROOT / "characters.json"
STYLE_FILE = ROOT / "style.txt"
IMAGES_DIR = ROOT / "images"
LOGS_DIR = ROOT / "logs"

# gpt-image-2.5-sunburst: 품질 우선 / gpt-image-2.5-flare: 속도 우선 / gpt-image-2: 이전 세대
DEFAULT_MODEL = "gpt-image-2.5-sunburst"
DEFAULT_SIZE = "1024x1536"  # 2:3 세로
DEFAULT_QUALITY = "high"

MAX_RETRIES = 3
RETRY_WAIT_SEC = 5
CALL_INTERVAL_SEC = 2

REFERENCE_INSTRUCTION = (
    "Use the provided reference image ONLY as an art-style reference "
    "(rendering, line quality, coloring, lighting mood). "
    "Do not copy its character, pose, outfit, or composition. Draw the new character described below."
)


def load_characters():
    with open(CHARACTERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_style():
    return STYLE_FILE.read_text(encoding="utf-8").strip()


def build_prompt(char, style, with_reference=False):
    parts = []
    if with_reference:
        parts.append(REFERENCE_INSTRUCTION)
    parts.append(style)
    parts.append(f"Character: {char['job']}, reimagined as an RPG {char['class']}.")
    parts.append(f"Color palette: {char['palette']}.")
    parts.append(f"Scene: {char['scene']}.")
    return "\n".join(parts)


def output_path(char):
    return IMAGES_DIR / f"{char['id']:02d}_{char['name_en']}.png"


def write_log(log_file, record):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def call_api(client, prompt, args):
    params = dict(
        model=args.model,
        prompt=prompt,
        size=args.size,
        quality=args.quality,
        output_format="png",
        n=1,
    )
    if args.reference:
        with open(args.reference, "rb") as ref:
            result = client.images.edit(image=[ref], **params)
    else:
        result = client.images.generate(**params)
    return base64.b64decode(result.data[0].b64_json)


def generate_one(client, char, prompt, args, log_file):
    path = output_path(char)
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        started = datetime.now().isoformat(timespec="seconds")
        try:
            image_bytes = call_api(client, prompt, args)
            path.write_bytes(image_bytes)
            write_log(log_file, {
                "time": started, "id": char["id"], "name": char["name_en"],
                "model": args.model, "size": args.size, "quality": args.quality,
                "reference": args.reference, "attempt": attempt,
                "result": "success", "file": str(path.relative_to(ROOT)), "prompt": prompt,
            })
            print(f"  [OK] {path.name} (시도 {attempt})")
            return True
        except Exception as e:  # noqa: BLE001 - API/네트워크 오류 전부 재시도 대상
            last_error = f"{type(e).__name__}: {e}"
            write_log(log_file, {
                "time": started, "id": char["id"], "name": char["name_en"],
                "model": args.model, "attempt": attempt,
                "result": "error", "error": last_error, "prompt": prompt,
            })
            print(f"  [실패] 시도 {attempt}/{MAX_RETRIES}: {last_error}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SEC * attempt)
    print(f"  [포기] #{char['id']:02d} {char['name_en']}: {last_error}")
    return False


def parse_args():
    p = argparse.ArgumentParser(description="현실 직업 RPG 도감 캐릭터 일러스트 생성기")
    p.add_argument("--dry-run", action="store_true", help="이미지 생성 없이 조립된 프롬프트만 출력")
    p.add_argument("--only", type=int, nargs="+", metavar="ID", help="지정한 번호만 (덮어쓰기) 재생성")
    p.add_argument("--reference", metavar="IMAGE", help="화풍 참고용 기준 이미지 경로 (png/jpg/webp)")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"이미지 모델 (기본: {DEFAULT_MODEL})")
    p.add_argument("--size", default=DEFAULT_SIZE, help=f"이미지 크기 (기본: {DEFAULT_SIZE})")
    p.add_argument("--quality", default=DEFAULT_QUALITY,
                   help=f"low / medium / high / xhigh / max / auto (기본: {DEFAULT_QUALITY})")
    return p.parse_args()


def main():
    args = parse_args()
    characters = load_characters()
    style = load_style()

    if args.only:
        wanted = set(args.only)
        unknown = wanted - {c["id"] for c in characters}
        if unknown:
            sys.exit(f"characters.json에 없는 번호: {sorted(unknown)}")
        characters = [c for c in characters if c["id"] in wanted]

    if args.reference and not Path(args.reference).is_file():
        sys.exit(f"기준 이미지를 찾을 수 없습니다: {args.reference}")

    if args.dry_run:
        for c in characters:
            print(f"===== #{c['id']:02d} {c['title']} -> {output_path(c).name} =====")
            print(build_prompt(c, style, bool(args.reference)))
            print()
        mode = f"images.edit (reference={args.reference})" if args.reference else "images.generate"
        print(f"[dry-run] {len(characters)}개 / model={args.model} size={args.size} "
              f"quality={args.quality} / {mode}")
        return

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다.")

    from openai import OpenAI  # dry-run에는 SDK가 필요 없도록 지연 import

    client = OpenAI()
    IMAGES_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / f"generate_{datetime.now():%Y%m%d_%H%M%S}.jsonl"

    ok = skipped = failed = 0
    called = False
    for c in characters:
        path = output_path(c)
        if path.exists() and not args.only:
            print(f"[건너뜀] {path.name} 이미 존재")
            skipped += 1
            continue
        if called:
            time.sleep(CALL_INTERVAL_SEC)
        print(f"[생성] #{c['id']:02d} {c['title']} ({c['job']})")
        prompt = build_prompt(c, style, bool(args.reference))
        if generate_one(client, c, prompt, args, log_file):
            ok += 1
        else:
            failed += 1
        called = True

    print(f"\n완료: 성공 {ok} / 건너뜀 {skipped} / 실패 {failed}  (로그: {log_file.relative_to(ROOT)})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
