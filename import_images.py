#!/usr/bin/env python3
"""ChatGPT 웹에서 받은 이미지를 images/{id:02d}_{name_en}.png 로 정리.

다운로드 폴더의 이미지를 '다운로드한 시각' 순으로 정렬해, 아직 이미지가 없는
캐릭터 번호에 차례로 배정합니다. 기본은 미리보기만 하고 --apply 를 붙여야 복사합니다.

    python import_images.py ~/Downloads --since 30          # 최근 30분 파일 미리보기
    python import_images.py ~/Downloads --since 30 --apply  # 실제 복사
    python import_images.py ~/Downloads/a.png --id 5 --apply  # 한 장을 5번으로 지정
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

from generate import IMAGES_DIR, load_characters, output_path

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def main():
    p = argparse.ArgumentParser(description="다운로드한 이미지를 도감 파일명으로 정리")
    p.add_argument("source", help="다운로드 폴더 또는 이미지 파일 하나")
    p.add_argument("--id", type=int, help="source가 파일 하나일 때 배정할 번호 (기존 파일 덮어씀)")
    p.add_argument("--since", type=float, metavar="MIN", help="최근 N분 안에 받은 파일만 대상")
    p.add_argument("--apply", action="store_true", help="실제로 복사 (없으면 미리보기만)")
    args = p.parse_args()

    chars = {c["id"]: c for c in load_characters()}
    src = Path(args.source).expanduser()

    if args.id is not None:
        if not src.is_file() or args.id not in chars:
            sys.exit("--id 는 존재하는 이미지 파일 하나와 characters.json의 번호가 필요합니다.")
        pairs = [(src, chars[args.id])]
    else:
        if not src.is_dir():
            sys.exit(f"폴더를 찾을 수 없습니다: {src}")
        files = [f for f in src.iterdir() if f.is_file() and f.suffix.lower() in EXTS]
        if args.since:
            cutoff = time.time() - args.since * 60
            files = [f for f in files if f.stat().st_mtime >= cutoff]
        files.sort(key=lambda f: f.stat().st_mtime)
        missing = [c for _, c in sorted(chars.items()) if not output_path(c).exists()]
        pairs = list(zip(files, missing))
        if len(files) > len(missing):
            print(f"[주의] 남는 파일 {len(files) - len(missing)}개는 무시됩니다.")

    if not pairs:
        print("배정할 파일이 없습니다.")
        return

    for f, c in pairs:
        dest = output_path(c)
        convert = f.suffix.lower() != ".png"
        print(f"{f.name}  ->  {dest.name}" + ("  (PNG로 변환)" if convert else ""))
        if not args.apply:
            continue
        IMAGES_DIR.mkdir(exist_ok=True)
        if convert:
            try:
                from PIL import Image
            except ImportError:
                sys.exit("PNG가 아닌 파일 변환에는 Pillow가 필요합니다: pip install pillow")
            Image.open(f).save(dest, "PNG")
        else:
            shutil.copy2(f, dest)

    print("\n복사 완료. python gallery.py 로 갤러리를 갱신하세요." if args.apply
          else "\n미리보기입니다. 맞으면 --apply 를 붙여 다시 실행하세요.")


if __name__ == "__main__":
    main()
