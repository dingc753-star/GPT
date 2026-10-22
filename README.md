# 현실 직업 RPG 도감 - 캐릭터 일러스트 자동 생성기

현실 직업을 근미래 SF RPG 캐릭터로 재해석한 일러스트를 OpenAI 이미지 API로 한 장씩 순서대로 생성합니다.

## 구성

| 파일 | 설명 |
| --- | --- |
| `characters.json` | 캐릭터 목록 (`id`, `name_en`, `title`, `job`, `class`, `palette`, `scene`) |
| `style.txt` | 모든 캐릭터에 공통으로 붙는 스타일 문장 |
| `generate.py` | 이미지 생성 스크립트 |
| `prompt_pack.py` | ChatGPT 웹용 복사 버튼 프롬프트 모음 `prompts.html` 생성 |
| `import_images.py` | 다운로드한 이미지를 도감 파일명으로 정리 |
| `gallery.py` | `images/`를 카드 그리드로 보여주는 `gallery.html` 생성 |
| `images/` | 생성 결과 (`{id:02d}_{name_en}.png`) |
| `logs/` | 실행별 로그 (`generate_YYYYMMDD_HHMMSS.jsonl`: 시각, 프롬프트, 결과) |

- `name_en`은 파일명에 쓰는 영문 이름입니다.
- `title`은 갤러리 카드에만 표시되며, 이미지에 글자가 들어가지 않도록 프롬프트에는 넣지 않습니다.

## 설치

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."      # Windows PowerShell: $env:OPENAI_API_KEY="sk-..."
```

API 키는 코드에 넣지 않고 환경변수에서만 읽습니다.

## 사용법

```bash
# 1) 프롬프트 미리보기 (API 호출 없음, 키 불필요)
python generate.py --dry-run
python generate.py --dry-run --only 3

# 2) 전체 생성: 없는 파일만 순서대로 생성하고, 이미 있는 파일은 건너뜀
python generate.py

# 3) 특정 번호만 재생성 (기존 파일 덮어쓰기)
python generate.py --only 1 2

# 4) 기준 이미지를 화풍 참고로 사용
python generate.py --reference images/01_RobotFleetPM.png --only 2 3

# 5) 갤러리 만들기 -> gallery.html을 브라우저로 열기
python gallery.py
```

### 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--dry-run` | - | 조립된 프롬프트만 출력 |
| `--only ID [ID ...]` | - | 지정한 번호만 생성 (기존 파일이 있어도 덮어씀) |
| `--reference IMAGE` | - | 화풍 참고 이미지. `images.edit` 엔드포인트에 입력 이미지로 전달 |
| `--model` | `gpt-image-2.5-sunburst` | `gpt-image-2.5-flare`(속도 우선), `gpt-image-2` 등 |
| `--size` | `1024x1536` | 2:3 세로. gpt-image-2 계열은 16의 배수로 된 임의 크기 지원 (예: `1344x2016`) |
| `--quality` | `high` | `low` / `medium` / `high` / `auto`. 2.5 계열은 `xhigh`, `max`도 지원 |

### 동작 방식

- 캐릭터를 하나씩 순서대로 생성하고, 호출 사이에 2초 대기합니다.
- 실패하면 최대 3회까지 재시도합니다 (재시도 대기 5초, 10초).
- `--reference` 모드에서는 프롬프트 맨 앞에 "참고 이미지는 화풍만 따르고 캐릭터·포즈·구도는 따라 하지 말 것" 지시를 붙입니다.
- 모든 시도(성공/실패)는 `logs/`에 JSON Lines 형식으로 기록됩니다.

## API 없이 ChatGPT 웹으로 만들기 (반자동)

API 키 없이 ChatGPT 구독(웹)으로 생성하는 방법입니다. 복사·붙여넣기와 다운로드는 직접 하고, 프롬프트 조립과 파일 정리는 스크립트가 맡습니다.

```bash
# 1) 복사 버튼이 달린 프롬프트 모음 만들기 -> prompts.html을 브라우저로 열기
python prompt_pack.py
python prompt_pack.py --only 1 2          # 테스트용 2개만
python prompt_pack.py --reference         # 기준 이미지를 채팅에 첨부할 때 (화풍 참고 지시문 포함)

# 2) chatgpt.com 새 채팅에 맨 위 [ALL] 카드를 붙여넣기 -> 이미지가 나오면 다운로드 후 "next" 입력 반복
#    (특정 캐릭터만 다시 만들 때는 개별 카드를 복사)

# 3) 다운로드 폴더의 이미지를 받은 순서대로 아직 없는 번호에 배정
python import_images.py ~/Downloads --since 30           # 최근 30분 파일 미리보기
python import_images.py ~/Downloads --since 30 --apply   # 실제 복사
python import_images.py ~/Downloads/xxx.png --id 5 --apply   # 한 장을 특정 번호로 지정 (덮어씀)

# 4) 갤러리 갱신
python gallery.py
```

- 화풍을 맞추려면 한 채팅방에서 이어서 생성하거나, 마음에 드는 첫 장을 매번 첨부하세요.
- PNG가 아닌 파일(webp 등)을 변환하려면 `pip install pillow`가 필요합니다.
- ChatGPT 웹 화면을 스크립트로 자동 조작하는 것은 OpenAI 이용약관(자동화된 출력 추출 금지)에 어긋날 수 있어 넣지 않았습니다. 완전 자동이 필요하면 위의 API 방식을 쓰세요.

## 비용 팁

- 먼저 `--dry-run`으로 프롬프트를 확인하세요.
- 시험 생성은 `--only 1 2 --quality medium`처럼 소량·저품질로 하세요.
- 화풍이 마음에 드는 한 장을 고른 뒤 `--reference`로 나머지를 생성하면 도감 전체의 톤이 맞춰집니다.
