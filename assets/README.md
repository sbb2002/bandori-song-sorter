# assets 디렉터리 규칙

이미지 에셋의 배치·네이밍 규칙입니다. **원본 데이터는 `src/content/songs/*.yaml`** (밴드당 1파일)이며,
`*.csv`는 converter 산출물이라 추적하지 않습니다(`.gitignore`).

## 레이아웃 (종류별)

에셋은 **종류별**로 나눕니다. 파일명의 `<band>`는 `src/content/songs/*.yaml`의 `band:` 키와
**정확히 일치**해야 합니다(소문자 snake_case).

| 경로 | 용도 | 쓰는 곳 |
|---|---|---|
| `assets/icons/<band>.png` | 밴드 셀렉터·히트맵 아이콘 | `static/js/script.js` `bandIcon()` |
| `assets/icons/_fallback.png` | 아이콘 누락 시 대체 | (구 `undefined.png`) |
| `assets/bands/<band>.png` | 다운로드 단체사진 | `script.js` 다운로드 |
| `assets/albums/<band>/*.webp` | 앨범 커버 | `src/content/songs/*.yaml`의 `img_url` (※ 현 v2 화면 미사용, **legacy 보존**) |

### 포맷·기타
- 포맷은 **webp 우선**. 아이콘/단체사진은 png 허용. jpg는 webp로 통일.
- `temp.*` 같은 placeholder는 커밋하지 않음(없으면 `_fallback`으로 대체).
- 같은 이미지의 중복 포맷(예: png+webp 둘 다)은 두지 않음.
- `albums/<band>/`의 **기존** 커버 파일명은 `aNN`(정규)·`mNN`(미니) 번호 체계를 유지함(일본어 앨범명은 슬러그화가 깔끔치 않아 번호 유지). 새로 추가하는 커버는 의미 있는 슬러그 권장(예: `1st_one-of-us.webp`).

## 밴드 추가 체크리스트
1. `src/content/songs/<band>.yaml` 작성 (`band:` 키 결정).
2. `assets/icons/<band>.png` 추가.
3. `assets/bands/<band>.png` 추가(다운로드용).
4. (선택) `assets/albums/<band>/...` 앨범 커버 + yaml `img_url` 연결.
5. `python src/build.py` 재실행.

## 현황 (2026-06-20, 1단계 완료)

위 종류별 레이아웃으로 **재배치 완료**. `git mv`로 이력 보존(rename 65 + 삭제 15).

- **아이콘**: `assets/icons/<band>.png` 13개 + `_fallback.png`(구 `undefined.png`).
- **단체사진**: `assets/bands/<band>.png` 12개. 미사용 `band.webp`는 전부 삭제. (`various_artists`는 단체사진이 원래 없음.)
- **앨범 커버**: `assets/albums/<band>/...`로 이동, 파일명(`aNN`/`mNN`) 유지. `etc/*` → `albums/various_artists/`. **legacy 보존**(v2 미표시).
- **동시 수정**: `static/js/script.js` 2곳(아이콘·단체사진 경로) + 전 `src/content/songs/*.yaml` `img_url` + `build.py` 재빌드(곡 488). 무결성 검증 통과(고유 `img_url` 40개 전부 추적 파일로 연결).

### 남은 정리(선택)
- jpg 미변환 잔존: `albums/raise_a_suilen/a02.jpg`, `albums/various_artists/{chispa,glitter_green}.jpg` → webp 통일 권장.
- `docs/index.html`(옛 v1)은 구 경로 하드코딩이라 이번 이동으로 깨짐 → 아카이브/방치 결정 필요(라이브 아님).
