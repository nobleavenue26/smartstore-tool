# Instagram 스킬 (ig-*)

`.claude/skills/ig-*` 13개 스킬은 [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill)
(MIT, 커밋 `d03c56b`)에서 가져왔습니다. 라이선스는 이 폴더의 `LICENSE`에 있습니다.

## 이 저장소에서 바꾼 것: 한국어 보정

원본 파이썬 도구는 영어 정규식(`\b`, 대문자 고유명사, 축약형, `comment WORD`)만 써서
한국어 캡션의 해시태그·CTA·숫자를 0개로 세는 문제가 있었습니다.

- `ig-human/ko.py`, `ig-human/ko.json`: 한국어 공용 모듈과 데이터 (브랜드, 긴장 단어, CTA,
  조사, 의미 없는 태그, 한국어 AI 문체 패턴). **운영하면서 직접 편집하세요.**
- `caption.py`, `hookscore.py`, `beats.py`, `detect.py`, `humanize.py`: 한글이 있을 때만
  `ko.py`를 씁니다. 영어 입력의 출력은 원본과 같습니다 (`caption.py`의 숫자 개수 하나만 다름:
  원본은 `$18,000`을 `$1`과 `000` 두 개로 셌습니다).
- `ig-viral/swipe.py`의 훅 공식 분류(`hooks.json`의 `match`)는 영어 전용 그대로라
  한국어 훅은 `unclassified`로 나옵니다.

## voice.md

스킬들은 `~/.claude/instagram/voice.md`를 읽습니다. 클라우드 세션에서는 홈 폴더가 세션마다
초기화되므로, 이 폴더의 `voice.md`를 채워 두고 세션 시작 시 복사해 쓰세요:

```bash
mkdir -p ~/.claude/instagram && cp .claude/instagram/voice.md ~/.claude/instagram/
```
