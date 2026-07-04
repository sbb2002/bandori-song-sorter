# src/ — 소스·데이터·도구

> 한 줄 원칙: **레포 루트 = 배포되는 사이트**(`index.html` · `static/` · `assets/`), **`src/` = 그 사이트를 만드는 모든 소스**(빌드 스크립트·입력 데이터·도구·테스트).
> GitHub Pages는 루트를 서빙한다. `src/` 안의 것은 런타임에 fetch되지 않고, `build.py`가 읽어 `index.html`에 구워넣거나(baking) 개발 시에만 쓰인다.

> 🗂 **(완료된 1회용 마이그레이션 · 아카이브)**: 루트→`src/` 구조 개편 당시, `git pull`이 옮기지 못하는 gitignore 데이터(옛 경로에 남은 오디오 캐시 등)를 새 경로로 옮기던 스크립트가 있었다 → `src/tools/legacy/migrate_local_cache.bat`. 개편이 끝난 지금은 새로 clone하는 로컬이 처음부터 `src/` 구조를 받으므로 **더 이상 실행할 필요가 없다**(옛 루트 경로에 남은 데이터가 없기 때문). 이력 보존용으로만 legacy에 둔다.

## 폴더 지도

| 경로 | 용도 |
|------|------|
| `src/build.py` | 빌드 오케스트레이터. `content/`를 읽어 **루트 `index.html`** 을 생성 |
| `src/templates/` | `index.html`의 Jinja2 템플릿(`index_template.html`) |
| `src/content/` | **빌드 입력 데이터**(런타임 fetch 없음 → index.html에 baking) |
| `src/content/songs/` | 밴드별 곡 카탈로그 (구 `data/`) |
| `src/content/wordcloud/` | 밴드별 워드클라우드 키워드 |
| `src/content/cluster/` | 음원맵 좌표 + 파일럿 산출물 |
| `src/tools/` | 데이터 생성·검수 스크립트 (용도별 하위폴더) |
| `src/tests/` | `static/js/core.js` 단위 테스트 |

## 명명·배치 규칙

### `content/songs/<band>.yaml`
- **파일 1개 = 밴드 1개.** 파일명 stem = 파일 안 `band:` 키 = `assets/icons/<band>.png` 와 일치시킨다.
- 구조: **앨범 리스트 → 앨범 → 트랙**.
  ```yaml
  - band: 'afterglow'
    numbering: '1st'          # 앨범 순번 or 'Single'/'Cover'
    album_title: 'ONE OF US'
    img_url: assets/albums/afterglow/a01.webp
    tracks:
      - track_number: '01'
        name: 'ON YOUR MARK'
        url: https://youtu.be/09B-WljIiTo
  ```
- **화면에 쓰이는 필드는 `band`·`name`·`url` 뿐.** `album_title`·`img_url`은 미표시(yaml 정리·provenance용). 신곡(single)의 `track_number`에는 발매일을 넣어 이력 보존.
- 편집 후 반드시 **`python src/build.py`** 재실행 → `index.html` 갱신.

### `content/wordcloud/<band>.yaml`
- 파일명 stem = 밴드. `{band, generated, song_count, keywords:[{jp, ko, weight}]}`.
- `ko`/`weight`는 **사용자 수동 검수본** → `build_keywords.py` 재생성 시 덮어써진다(가사 원문 있을 때만 재생성). 감성 극성은 `src/tools/wordcloud/senti_lexicon.yaml` 룩업으로 빌드 시 합쳐진다.

### `content/cluster/`
- `audio_map.json` — **커밋되는 음원맵 산출물**(`build_perceptual_map.py` 생성, build.py가 baking).
- `onsets/<band>__<idx>.json` — **커밋되는 재생 펄스 산출물**(`build_pulse_all.py` 생성: demucs 드럼분리→beat track).
- `songs_full.csv` — 전곡 매니페스트(`idx,band,song,url`, 660곡).
- `legacy/` — 실험 잔재(`songs_top10.csv` 97곡 프리뷰 서브셋, `axis_*.csv` 축 파일럿 워크시트).
- `audio_cache/`·`audio_full/`·`audio_drums/`·`_*` — **gitignore**(음원=저작물·임시 산출). `keywords_2d.json`만 예외 추적(레거시).

### `tools/<purpose>/`
성격에 맞는 하위폴더에 둔다:
| 폴더 | 성격 | 대표 스크립트 |
|------|------|---------------|
| `collect/` | 수집·백필 | `youtube_rss`, `youtube_api`, `backfill`, `insert_backfill`, `band_top10` |
| `curate/` | 검수·수정 | `verify_links`, `delete_redundant`, `resolve_empty`, `execute_placement`, `check_embeddable`, `apply_fix_url` |
| `convert/` | 포맷 변환 | `converter` (CSV↔YAML) |
| `cluster/` | 음원맵 파이프라인 | `build_perceptual_map`(현행) · `perceptual_features` · `axis_correlation` · `add_x_features` / `build_audio_map`·`build_embeddings`(구·폐기 후보) |
| `wordcloud/` | 가사→키워드 | `build_keywords`, `lyrics_parser` |
- 스크립트 전용 데이터 리소스(예: `senti_lexicon.yaml`, `*_cache.json`, `*.csv`)는 해당 tools 폴더에 함께 둔다.

### `tests/`
- `static/js/core.js`(중복제거·티어 스코어링·히스토그램/히트맵·공유링크 등 순수 로직) 단위 테스트.
- `npm test`(= `node --test`, **루트에서** 실행)가 `*.test.js`를 자동 발견. core.js 로직을 바꾸면 여기 테스트도 갱신.

## 경로 규칙 (스크립트 작성 시 중요)

모든 스크립트·빌드는 **레포 루트에서 실행**한다: `python src/build.py`, `python src/tools/<...>.py`, `npm test`.

- **신규 스크립트 권장 = 파일 위치 앵커링**(어느 CWD에서도 동작):
  ```python
  from pathlib import Path
  ROOT  = Path(__file__).resolve().parents[3]   # src/tools/<sub>/<file> → repo root
  SONGS = ROOT / "src" / "content" / "songs"    # 데이터
  ASSETS = ROOT / "assets"                       # assets·.env 는 루트에 있음
  ```
  `collect/`·`curate/` 스크립트가 이 방식이다.
- `build.py`는 `SRC = Path(__file__).parent`, `ROOT = SRC.parent`, `CONTENT = SRC/"content"`로 앵커. **산출 `index.html`은 루트**(배포 위치)에 쓴다.
- 일부 `cluster/`·`wordcloud/` 스크립트는 아직 **CWD 상대경로**(`Path("src/content/cluster/...")`)라 **반드시 레포 루트에서** 실행해야 한다. 신규 작성 시엔 위 앵커 방식을 권장.
- 캐시·비밀·저작물(오디오·가사)은 gitignore 대상. `.gitignore` 참고.

## 자주 쓰는 명령
```bash
python src/build.py     # content/ → 루트 index.html 재생성 (데이터 편집 후 필수)
npm test                # core.js 단위 테스트 (루트에서)
python -m http.server   # 루트에서 로컬 프리뷰 (index.html·static·assets 서빙)
```
