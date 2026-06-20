# assets 디렉터리 규칙

이미지 에셋의 배치·네이밍 규칙입니다. **원본 데이터는 `data/*.yaml`** (밴드당 1파일)이며,
`*.csv`는 converter 산출물이라 추적하지 않습니다(`.gitignore`).

## 레이아웃 (종류별)

에셋은 **종류별**로 나눕니다. 파일명의 `<band>`는 `data/*.yaml`의 `band:` 키와
**정확히 일치**해야 합니다(소문자 snake_case).

| 경로 | 용도 | 쓰는 곳 |
|---|---|---|
| `assets/icons/<band>.png` | 밴드 셀렉터·히트맵 아이콘 | `static/js/script.js` `bandIcon()` |
| `assets/icons/_fallback.png` | 아이콘 누락 시 대체 | (구 `undefined.png`) |
| `assets/bands/<band>.png` | 다운로드 단체사진 | `script.js` 다운로드 |
| `assets/albums/<band>/<numbering>_<slug>.webp` | 앨범 커버 | `data/*.yaml`의 `img_url` (※ 현 v2 화면 미사용, **legacy 보존**) |

### 포맷·기타
- 포맷은 **webp 우선**. 아이콘/단체사진은 png 허용. jpg는 webp로 통일.
- `temp.*` 같은 placeholder는 커밋하지 않음(없으면 `_fallback`으로 대체).
- 같은 이미지의 중복 포맷(예: png+webp 둘 다)은 두지 않음.

## 밴드 추가 체크리스트
1. `data/<band>.yaml` 작성 (`band:` 키 결정).
2. `assets/icons/<band>.png` 추가.
3. `assets/bands/<band>.png` 추가(다운로드용).
4. (선택) `assets/albums/<band>/...` 앨범 커버 + yaml `img_url` 연결.
5. `python build.py` 재실행.

## 현재 상태 / 이전 계획

아직 위 구조로 **이전 전(前)** 입니다. 현재 혼재 상태:

- **아이콘**: `assets/icon/<band>.png` (단수 `icon`) → `icons/`로 이전 예정. `undefined.png` → `_fallback.png`.
- **단체사진**: `assets/<band>/band.png` → `bands/<band>.png`로 이전 예정. `band.webp`는 미사용 → 제거 대상.
- **앨범 커버**: `assets/<band>/{a,m}NN.webp` (a=정규, m=미니) → `albums/<band>/`로 이전 예정. **legacy 보존**(v2 곡 단위 UI는 현재 미표시).
- `assets/etc/*`(various_artists 서브유닛 커버)도 `albums/various_artists/`로 편입 예정.

이전(1단계) 시 `static/js/script.js`(아이콘·단체사진 경로 2곳)와 모든 yaml `img_url`을
함께 수정하고 `python build.py` 후 라이브 확인이 필요합니다.
