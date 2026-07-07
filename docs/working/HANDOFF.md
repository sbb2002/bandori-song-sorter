# HANDOFF: bandori-song-sorter — 남은 작업

**이 문서 = 앞으로 할 일의 인덱스.** 각 작업은 요약 + 상세 레퍼런스 링크로만 구성한다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 단일 출처는 memory `wordcloud_quality_plan.md`.

마지막 갱신: **2026-07-07(세션 29)** — **작업 4(EMOI-MAP 딥스페이스/별 시각화) 완료·main 머지(`104e709` · done 29)**: 곡 점=곡 에너지 비례 글로우 별 + 뒤 canvas 별밭 + 밴드 성운 + Ave Mujica EMOI-MAP 전용 색(`#e64c8c`). **작업 5 신규 등록**: EMOI-MAP 좌표계 고찰(`docs/idea/260708-final_comment.md`) — 라벨 정직화·y축 에너지 토글·새 지각축(LRA/tempogram) 연구, **다음 세션 `feature/emoi-map-starfield`에서 이어감**.
이전: (세션 28) **작업 3 반자동 파이프라인 운영화·라이브**(done 28): 봇 정리(`/detect` deprecated·제거 · `/pause`+`/resume` 순서쌍 상쇄 · 감지 0곡도 알림) + **5분 폴러 폐지→단일 23:00 크론 통합**(`telegram-bot.yml` 제거, 명령 처리를 `pipeline.yml` 맨 앞으로 흡수 → 명령→감지→알림이 한 실행) + `src/tools/pipeline`·루트 `actions/` → **`src/tools/semiauto-loader/`** 통합(+폴더 README) + run_local 결과 실시간 로그·0건/반영/실패 구분·**로컬 처리 결과 텔레그램 통지**(notify가 repo 루트 `.env` 자동 로드).
> **⏭ 다음 = (선택) 분석-only 로컬 스크립트**(다운로드 이후 분석·push만 — 분석 라이브러리 없는 로컬 대비, § 작업 3 '남은 것') · DRM 1곡 수동. **반자동 본류는 완료·라이브.**
> ⏭ **작업 5 = EMOI-MAP 좌표계 고찰**(260708): 라벨 정직화·y축 에너지 토글·새 지각축 연구 — **다음 세션 `feature/emoi-map-starfield`에서 이어감**(문서 `docs/idea/260708-final_comment.md`, Phase A→B0→B→C). § 작업 5.
이전: (2026-07-06 세션 26~27) 작업 3 인프라 구축(감지→좌표→pulse→main + Pages 아티팩트 배포) + CI 다운로드 봇월 확정(E2E 3회) → 반자동(다운로드만 로컬 IP) 전환 결정. done 26~27.
이전: (2026-07-05 세션 25) 음원맵 클러스터링/재생펄스 완결 + main 머지: 전곡 **660곡** 좌표·펄스 + 렌더 lazy-fetch(index.html 0.30MB) + 에너지 동적 subdivision(음량→박/8분) + 볼륨 프리셋 4단계. done 24~25 · [report/emoi-cluster-pulse](report/emoi-cluster-pulse/README.md).
이전: (2026-07-04) 재생 펄스 파일럿 → 세션 23 방안 A 완성. (2026-07-03 17:00) 작업 1(D) 레이아웃 확정 + 정적파일 분할 main 머지(done 22).

---

## 시작 전 체크 (다른 로컬·세션)
> 1. `git pull origin main`(660곡). 작업은 **새 feature 브랜치**에서.
> 2. `.env`의 `YOUTUBE_API_KEY` = **장치별·비커밋**(gitignore) — 백필/지역락 점검 시 재추가(없으면 `insert_backfill.py`·`check_embeddable.py` 즉시 중단).
> 3. **node 필수**(yt-dlp nsig 서명해독 → 없으면 오디오 수집 403 다발 · `node --check` · `npm test`). 설치 = `conda install -c conda-forge nodejs`(세션 23에 이 장치 설치 완료).
> 4. 가사 원문 `assets/lyrics/<band>.md` = 로컬 전용(gitignore). 커밋된 `wordcloud/<band>.yaml`로 검수·렌더는 가능하나 `build_keywords.py` **재생성은 원문 .md 필요**.
> 5. 로컬 브랜치(2026-06-30 정리): `main` + 백업 3(`backup/main-20260620·22·30`) + `feature/ux-02-opt-a`(옵션A 유일본, 미머지·원격없음 — 삭제 금지).

---

## 현황
- 데이터 **677 트랙 / 화면 660곡(dedup) / 13밴드**. 워드클라우드 **라이브**, 백필(1-a/1-b)·지역락 처리 완료(done 14~20, 화면 526→660). 
- **레이아웃 확정 + 정적파일 분할 완료**(done 22, main 반영): 편집 시 CSS=`common/desktop/mobile.css`·JS=`static/js/functions/01~19-*.js` **분할 파일 직접 수정**(참조식 → 리빌드 불필요), 템플릿 변경만 `python src/build.py`.
- **작업 2(음원맵 전곡 확대) 완결·동결**(done 23): 659곡/13밴드 + `norm` 파라미터, HUD·펄스까지. 작업 브랜치 `feature/emoi-cluster-v3b`(미머지·푸시됨). **다음 본류 = 머지 + 작업 3(자동화 파이프라인)**.

## 우선순위
| 작업 | 상태 | 상세 |
|------|------|------|
| 1. 워드클라우드 | ✅ **완전 완료**(품질+배치 D · done 22) | § 작업 1 |
| 2. 음원맵 전곡 확대 | ✅ **완결·동결**(659곡·norm, done 23) | § 작업 2 |
| 3. 자동화 파이프라인 | ✅ **반자동 운영화 완료·라이브**(단일 크론 봇+감지+알림 · 로컬 처리·결과 Telegram) | § 작업 3 · [spec](spec/pipeline-automation.md) |
| 4. EMOI-MAP 딥스페이스/별 시각화 | ✅ **완료·main 머지**(104e709) | [done 29](done.md) |
| 5. EMOI-MAP 좌표계 고찰 | ✅ **A·B0·C 완료** — timbre×valence 확정·arousal 불가(실질 1.x차원) | § 작업 5 · [논문](../research/emotion-axes-extraction.md) |
| 보류 · 백로그 | 후순위 | § 보류·백로그 |

원칙: **밴드 시각화 마무리 → 후속 확장.** 보류·백로그는 별도 결정 사안.

---

## 병렬 실행 계획 (작업 2·3 — 2026-07-03 확정, 이 순서로 진행)

> ✅ **Phase 0~2 완료(done 23)** — 오디오 수집(659/660)·전곡 빌드·`norm` 동결 끝. 아래는 실행 기록(참고 보존). **남은 것 = Phase 3(머지 + C의 증분 append).**

> 오늘 작업 브랜치 = **`feature/emoi-cluster-v3a`**. 크리티컬 패스는 하나뿐: **범위 → 오디오 수집 → 전곡 빌드·동결 → 증분 append.** 나머지는 오디오 무관 → **오디오 수집 대기시간(로컬 ~30~90분 무인)에 병렬**로 굴린다.
>
> **⏸ 중단 시 재개(다른 로컬·세션)**: 각 페이즈/트랙은 독립 커밋 → `git push` 하면 다른 로컬이 이어받는다. **단 오디오 wav 캐시는 gitignore = 장치 전용** — 다른 로컬로 옮겨도 wav 는 안 따라온다(현재 이 장치엔 wav 0개). 다운로드를 다른 로컬에서 이어가면 그 장치 기준으로 재수집하되, `fetch_audio.py` 의 **skip-existing 으로 장치 내 재개는 보장**(끊겨도 같은 명령 재실행 = 남은 곡만).

**Phase 0 — 결정 + 빌드 준비 (동시)**
- **[사용자 게이트]** ① 범위 = **660 전곡 확정**(수집 진행 중) · ② 레이아웃 묶음 = ✅ **확정(대안 B, done 22)**.
- **[A·코드]** `build_perceptual_map.py`에 `--manifest` 인자 + 매니페스트 생성(`songs/*.yaml`→`band,idx,song,url`, dedup=vid, 캡N) + **정규화 파라미터 저장(contrast·mode의 mean/std + shift + overrides, pipeline §5)**. 셋 다 audio 없이 현행으로 스모크 가능. ⚠️ 이 저장 코드가 **다운로드 착수 전에** 들어가 있어야 전곡 빌드가 파라미터를 남긴다(안 남기면 나중에 전곡 재수집).

**Phase 1 — 대기시간 병렬 (핵심 구간)**
- **[A]** **오디오 수집 착수**: `python src/tools/cluster/build_manifest.py`(→ `songs_full.csv` 660곡, 생성 완료) → `python src/tools/cluster/fetch_audio.py --cache audio_full`. 재개 가능·fail-soft·10%마다 진행률/예상종료. **일시중지 조건(OR)**: 1) 429 재시도소진/연속실패, 2) 17시+ETA≥5h, **3) 성공용량 > `--stop-size-gb`(기본 7GB)** ← USB 7.25GB 대비(2026-07-03 추가, `total_gb` 진행JSON 기록). 안티봇 5원칙 = `docs/idea/260703.md`. ← 도는 동안 ↓ 병렬.
  > ⏸ **2026-07-03 17:00 = 조건2로 자동 일시중지**(1차 수집 11:08~17:00, branch v3a · `--no-cookies` · JS런타임 node). **최종: 285/660(43%) · 세션신규 278 · 실패 24 · `audio_full` ≈ 6.0 GiB**(reason=`clock>=17:00 & eta 6h49m>=5.0h`). 7.25GB USB 여유 → `audio_full` **폴더째 복사**(압축·번들 생략). 진행 실시간 = `src/content/cluster/fetch_progress.json`(매 곡 갱신). ※ `total_gb`는 이 세션이 조건3 이전 구버전이라 미기록(디스크 기준 6.0 GiB).
  > 💡 **압축 안 함(2026-07-03 실측 결정)**: WAV(PCM)는 Compress-Archive/zstd 모두 **~3%만** 압축(6.2GB→~6.0GB)되고 6.2GB zip에 ~4분 소요 → 무의미. 파일도 곡당 ~22MB·수백 개라 번들 이점 없음 + 단일 대용량 파일은 **FAT32 4GB 제한**에 걸림. → `audio_full` **폴더를 그대로** USB에 복사가 최선.
  > ⚠️ **실패 = 전부 HTTP 403**(수집 중 24건 표본, 429/삭제/비공개 0건). node 서명해독은 정상(→ format 251까지 진행)인데 **`android vr` 클라이언트의 오디오 URL을 CDN이 거부**하는 케이스 → 레이트리밋/영구실패 아닌 **복구 가능**. 재개 시 실패분에 **`--extractor-args "youtube:player_client=tv,web_safari,ios"`** 류로 클라이언트 바꿔 재시도 권장(본계정 쿠키 금지 → 클라이언트 변경이 1순위).
  > **다른 로컬 재개 선결**: ① `pip install yt-dlp imageio-ffmpeg` + **node 필수**(JS런타임 — 없으면 yt-dlp nsig 서명 실패로 403 다발; `--js-runtimes` 자동 연결) · ② 이 로컬 `audio_full` 폴더를 **압축·번들 없이 그대로** USB로 복사 → 다른 로컬 `src/content/cluster/audio_full/`에 복사(WAV ~3%만 압축 → 압축 무의미) · ③ `python src/tools/cluster/fetch_audio.py --cache audio_full --no-cookies`(skip-existing 재개; 조건3 7GB 상한 자동 적용). ⭐ **오디오 48kHz 항상 유지**(용량 무관·다운샘플 금지, 사용자 확정 2026-07-03).
- **[B]** 렌더 최적화(ECharts `large`/`largeThreshold`/`progressive` + 줌/팬 + ALL z-order) + UX(센트로이드 클릭 비활성 + opacity 0.3). `static/js/script.js`만 → 리빌드 불필요. 현행 97곡/목업으로 개발.
- **[C]** 구 파일 폐기(`keywords_2d.json`·`build_embeddings.py`·`build_audio_map.py` + untracked `rss_seen/inbox/verify_cache`) + `actions/` 오케스트레이터 골격(collect[1–3]→cluster[**stub**]→stage[4–7]) + Phase 1.5 워크플로우.

**Phase 2 — 합류 (오디오 완료 후, 직렬)**
- **[A]** 전곡 빌드 `build_perceptual_map.py --cache audio_full` → `audio_map.json` + **파라미터 동결·저장**. `BAND_OVERRIDES`(morfonica)·`y_shift` 육안 재점검 → **여기서 상수 확정·동결**(= 마지막 튜닝 순간, fullscale §4 · pipeline §6) → 이후 오디오 폐기. `python src/build.py`.

**Phase 3 — 통합**
- B(렌더) ↔ A(전곡 `audio_map.json`) 머지 → 브라우저 실검수(`http.server` · 모바일 320px).
- C의 cluster stub → **동결 파라미터 기반 증분 append** 완성(pipeline §5).
- 레이아웃 결정 반영(작업 1-D + 음원맵 게시).
- 머지 경로: `feature/emoi-cluster-v2` → `feature/emoi-cluster` → `main`.

**트랙 충돌면**: A=`build_perceptual_map.py`+`audio_map.json` / B=`script.js` / C=신규·삭제 → 거의 무충돌. 공유물 `audio_map.json`(A 재생성, B 읽음)은 Phase 3에서 B를 A 결과 위로 정리.

---

## 작업 1. 워드클라우드 — ✅ 완전 완료
품질(2-c A·B·C + 키워드 색상) **완료**(done 20) + **(D) 배치 확정**(done 22): 음원맵 슬롯을 세로 분할선으로 좌=음원맵/우=워드클라우드(**대안 B**), 상시 렌더. 재생성 명령·큐레이션 주의(`weight:0`은 렌더 `||1`로 부활 → 제거는 yaml 줄 삭제 / `ko`는 재생성 시 덮어써짐)는 memory `wordcloud_quality_plan.md`·done 17·20.

## 작업 2. 음원맵 전곡 확대 — ✅ 완결·동결 (done 23)
**채택 축**: x=contrast(거칢↔매끄러움 r−0.81) · y=mode(밝음↔어두움 r+0.51). **전곡 659곡/13밴드 빌드·동결 완료**: `build_perceptual_map.py --manifest src/content/cluster/songs_full.csv --cache audio_full` → `audio_map.json`(+ `norm` 파라미터: contrast·mode의 mean/std/k/clip+shift+overrides+formula) → `build.py`. 렌더 = `16-audiomap.js _clDraw`(+HUD·펄스).
- 근거·상세: fullscale §4·§6 · pipeline §5 · axes([spec/audio-map-axes.md](spec/audio-map-axes.md)).

### 2-잔여
- **머지·실검수**: `feature/emoi-cluster-v3b` → `feature/emoi-cluster` → `main`(라이브 sbb2002.github.io). 머지 전 `python -m http.server`로 음원맵·HUD·펄스 + 모바일 320px 실검수.
- **오디오 캐시 폐기 가능**(`audio_full` 659곡 — 동결 완료, 커밋되는 건 파생 좌표뿐).
- roselia `競宴Red×Violet` 1곡(DRM) → 작업 3 증분으로.
- ✅ 완료: UX 센트로이드 클릭 비활성+반투명(done 23), HUD·펄스 연출.
- (선택) 구 미사용 폐기: `keywords_2d.json` · `build_embeddings.py` · `build_audio_map.py`.

## 작업 3. 자동화 파이프라인 — 신곡 로더 (✅ 반자동 · 운영화 완료·라이브)
**상세 구현·배선 = [done.md](done.md) 세션 26·27·28.** 설계 = [spec/pipeline-automation.md](spec/pipeline-automation.md). 작업 2(전곡 빌드+`norm` 동결)에 의존 — 완료됨.

### ⛔ 결론 — CI 다운로드는 봇월로 불가(실증 확정, 2026-07-06)
E2E dry-run으로 CI 오디오 다운로드를 검증한 결과 **GitHub Actions(데이터센터 IP)에서 YouTube 다운로드가 봇월("Sign in to confirm you're not a bot")에 막힘**이 확정:
- run `28789165878` 기본(android vr) hard-block → run `28789906761` **클라이언트 로테이션**(tv,web_safari,ios) 전부 hard-block → run `28791454189` **PO 토큰**(bgutil provider, 익명 visitor) web_safari/tv/mweb 전부 hard-block.
- 벽은 **클라이언트가 아니라 IP 평판**. spec §4 카드 ①(최신 yt-dlp)·②(로테이션)·PO토큰까지 소진. Render 등 다른 클라우드도 전부 데이터센터 IP라 동일(도망 불가).
- ★단 **다운로드 이후(demucs·pulse·좌표·커밋·배포)는 네트워크 게이트 없음** → E2E가 다운로드 直前까지 전 스텝 green으로 실증. **다운로드만 레지덴셜(집) IP로 빼면 나머지는 100% 자동.** 집 IP 다운로드는 전곡 660 벌크로 이미 실증.

### 🔧 채택 아키텍처 — 반자동(Actions 감지·알림 + 로컬 원커맨드 처리)
계획 원본 = `~/.claude/plans/floofy-tickling-corbato.md`. 흐름:
1. **(Actions, 매일 23:00 KST = cron `0 14 * * *`, 단일 실행)** ① 대기 중이던 Telegram 명령 처리(help/status/pause/resume) → ② paused 아니면 `orchestrate.py --detect-only --notify` 감지 → **감지 결과 Telegram 1건(신곡 N곡 요약 / 0곡이면 "0곡 발견" 도 전송)**. 다운로드 안 함.
2. **(Local, 사용자 트리거)** 알림 받고 `run_local.py` → 다운로드(집 IP)→demucs/pulse→좌표 append→`push origin main` → `deploy.yml` 자동 배포. **결과(0건/N곡 반영/실패)를 터미널 + Telegram 통지.**

**격리 원칙**: 자동화 git 활동(main 커밋·푸시)이 데브 핫픽스와 안 얽히도록 **전용 로컬 클론에서만 실행**(별개 브랜치로는 워킹트리 공유라 격리 안 됨 / 별도 GitHub 레포는 과함 — 데이터는 이 레포로 push돼야 deploy됨). 코드는 `src/tools/semiauto-loader/`에 두어 버전관리.

### 컴포넌트 (전부 `src/tools/semiauto-loader/`, 세션 28에 `pipeline`→개명 + 루트 `actions/` 흡수)
- `.github/workflows/pipeline.yml` — **단일 23:00 크론**: 명령 처리 → 감지 → 알림. `contents:write`(pause 상태 커밋). `TELEGRAM_BOT_TOKEN`·`TELEGRAM_CHAT_ID` secrets. (구 `telegram-bot.yml` 5분 폴러는 세션 28에 제거·흡수.)
- `orchestrate.py`(루트 `actions/`에서 이동, ROOT `parents[3]` 재계산) — 감지·처리·커밋 엔진. `--detect-only`/`--notify`(0곡도 전송)/`--notify-test`/`--dry`/`--test-*`.
- `run_local.py` — 사용자 원커맨드. 전용 클론(기본 `../bandori-pipeline`)을 `origin/main`로 reset → cwd=클론에서 `orchestrate.py` 실행. 결과를 실시간 스트리밍 + 종료 후 0건/반영/실패 구분 메시지 + `notify.send_telegram`. 인자 `--repo-path/--limit/--dry/--test-band/--test-video`.
- `notify.py` — `send_telegram()`(urllib 무의존). **repo 루트 `.env` 자동 로드**(환경변수 우선, python-dotenv 무의존): CI는 secrets로 no-op, 로컬은 `.env`의 토큰 사용. 토큰 없으면 조용히 스킵.
- `telegram_bot.py` — 명령 봇(아래). `bot_state.json` — pause 상태(이 폴더). `requirements.txt` — 오디오 스택 의존성(로컬 `pip install -r`).
- `deploy.yml` **무변경**(로컬 push가 트리거).

### 로컬 사용법
```
python src/tools/semiauto-loader/run_local.py                       # 감지→다운로드~push (실제 반영, 결과 Telegram)
python src/tools/semiauto-loader/run_local.py --dry                 # 처리하되 push 안 함(검증, Telegram 안 함)
python src/tools/semiauto-loader/run_local.py --test-band afterglow --test-video 09B-WljIiTo  # E2E 1곡(dry 강제)
```
사전조건: **한 env**에 오디오 스택(`pip install -r src/tools/semiauto-loader/requirements.txt` = yt-dlp·demucs/torch·librosa·soundfile·numpy·scipy·imageio-ffmpeg) + **node**(PATH, nsig 서명) + git push 자격. 로컬 Telegram 통지는 `.env`에 `TELEGRAM_BOT_TOKEN`·`TELEGRAM_CHAT_ID`(없으면 통지만 스킵). 상세 = 폴더 README.

### Telegram 명령 봇 (라이브)
상시 서버 없이 Telegram 명령을 **`pipeline.yml` 일일 크론 맨 앞 단계**에서 처리(`telegram_bot.py`, `getUpdates`+ack 무상태·**인가 chat_id만**). 세션 28에 5분 폴러 폐지 → 명령 응답은 최대 하루 지연이지만 pause/resume은 다음 감지 실행에 확실히 반영됨.
- `/help` · `/status`(주기·상태) · `/pause` · `/resume`. **`/detect`는 deprecated·제거**(감지는 크론이 자동 수행).
- **`/pause`→`/resume` 순서쌍 상쇄**: 한 실행에 둘 다 밀려오면 서로 상쇄되는 조작이라 무효 처리(상태변경·응답 없이 skip) + "함께 도착해 상쇄" 안내 1건.
- 일시정지 = `bot_state.json {paused}`(이 폴더, deploy 경로 밖, 봇이 [skip ci] 커밋). 같은 실행의 감지 단계가 읽어 paused면 감지·알림 skip.

### 상태 — ✅ 반자동 + 봇 운영화 완료·라이브
- ✅ 구현·머지(main): 단일 크론 통합 pipeline.yml · run_local.py(실시간 로그·결과 Telegram) · notify.py(.env 자동로드) · orchestrate(0곡 알림) · telegram_bot.py(/detect 제거·상쇄).
- ✅ 검증: 상쇄 실운영(run 28835461588·28835571685) · 로컬 Telegram 통지(`.env` 키 오타 수정 후 send 성공) · secrets 등록.

### 남은 것 (선택·후순위)
- **(사용자 요청) 분석-only 로컬 스크립트**: 다운로드는 다른 로컬/수단으로 받고, 분석~push만 하는 별도 파일. 일부 로컬은 분석 라이브러리(torch/demucs 등) 구동 환경이 안 될 수 있어 다운로드/분석 역할 분리가 필요. **현재 `run_local.py`(다운로드+분석 일체형)는 유지**하고 추가.
- DRM `roselia 競宴Red×Violet`: yt-dlp 취득 불가 → fail-soft 스킵(수동).
- (선택) 영구실패 재시도 상한 가드 · index.html `git rm --cached`(Option A 완전화) · 옛 프로토타입 잔재(`rss_seen.json`·`rss_inbox.csv`·`verify_cache.json`) 삭제.

---

## 작업 5. EMOI-MAP 좌표계 고찰 — ✅ Phase A·B0·C 완료 (timbre×valence 확정 · arousal 독립축 불가)
> **브랜치 분리**: Phase A(맵 정직화·energy 노출·n=1 처방) = `feature/emoi-map-starfield`(커밋 a6ad2bf, 푸시됨). Phase B0(onset 스크리닝) = `feature/emoi-cluster-energy-tempo`(커밋 98290d9, 푸시됨). **Phase C(정식 오디오 3정서축) = `feature/emoi-starfield-timbre-valence`**(현재).
Millsage·Ikka 1곡 밴드 좌표가 귀와 어긋남 → 근본 원인 = **실질 1.x차원**(contrast가 밝음·거칢 양쪽 지배) + **energy/tempo 지각축 feature 부재**(cluster-correlation 보고서).
- **문서(실행 기준)** = `docs/idea/260708-final_comment.md`(fable×opus 통합). 원 문제 `260708.md` · 개별 코멘트 `260708-{fable,opus}_comment.md`.
- **참고(작업 4 연계 · done 29)**: 별 시각화가 베이스 — `16-audiomap.js`(`songMark`·`_clSky*`/`_clBuildStarfield`·`_clSetNebula`) + 곡 `energy`가 `add_energy.py`로 `songs[].energy`에 이미 baked(660/660). Phase A(범례·라벨)·B(`y_energy` 토글)가 이 위에 얹힘.
- **✅ Phase A 완료**(2026-07-07 · 미커밋): ① 축 라벨 괄호 한정 — `axes.x` 거칢(음색)/매끄러움(음색), `axes.y` 밝음(장조)/어두움(단조)(리듬거칢·경쾌=밝음 오독 차단). ② energy 노출 — 툴팁 `· 에너지 NN%`(`songMark._e`) + 헤더 범례 칩 `★ 밝기·크기 = 곡 에너지`(`_clBuildEnergyLegend`, `.am-legend`) + **코어 색 명도 = energy**(고=밝게·저=어둡게, `_clEnergyColor` L 0.40~0.82·hue/채도 유지, `_clPulseColor` L오버라이드 재사용). ↳ ave_mujica EMOI-MAP 색 오버라이드(#e64c8c 로즈) 제거 → 원 지정색 #881144(와인) 복귀(명도 변조가 가시성 보정 대체, `CL_COLOR_OVERRIDE={}`). ③ n=1 처방 — **millsage dx=−18**(x 13.93→−4.07, 매끄러움), **ikka dy=+18**(y −9.28→+8.72, 밝음/경쾌); nudge=1지각점≈18좌표(k=25·σ≈24·r회귀). overrides+norm.overrides+baked좌표(곡·centroid)+`BAND_OVERRIDES` 상수 일관 기록, **만료=n≥5 시 제거**. 잠정 별 = centroid n<3 반투명(×0.5)+툴팁 `n=1 · 잠정`. 변경: `audio_map.json`(+build.py)·`16-audiomap.js`·`desktop.css`·`mobile.css`·`build_perceptual_map.py`. 브라우저 실검수 통과(축4·범례·잠정별·재배치·회귀 격자/HUD/별밭).
- **✅ Phase B0 완료**(2026-07-07 · 전멸): onset 파생 후보 9종(E1 mean·E2 LRA근사·E3 온셋밀도·dyn std/p90/p10·ACF pulse_bpm·librosa tempo) × 손라벨 energy/tempo(n=30) 상관 — **PASS 0/9**. 최강 `dyn_std`×energy r=−0.40(임계 미만·부호반대)·`pulse_bpm`×tempo r=+0.12. 원인 = **dyn.v가 곡별 정규화값**(펄스 연출용)이라 곡 간 절대에너지 씻김(doc §2 '뭉침' 예측 확증) + 온셋/ACF는 지각 템포 아님. → **Phase C 직행 확정**(정식 LUFS·tempogram, 오디오 원본 필요). 산출: `report/cluster-energy-axis/`(README·onset_features.csv 660·b0_correlation.{txt,json}·b0_screening.png). 도구: `src/tools/cluster/b0_{onset_features,correlate,plot}.py`. 진행관측 = `b0_progress.json`(곡마다 진행률·ETA·마지막곡, `b0_control.json`{command:pause}로 협조적 중단·재개). **⚠️ audio_full 폐기 금지**(C가 원본 재필요).
- **✅ Phase C 완료**(2026-07-07 · **timbre×valence 확정 / arousal 불가**): 원본 audio_full에서 정식 feature 18종(lufs·lra·rms_std·crest·tempo_acf·pulse_clarity·vbl·onset_rate·mode·harmonic·centroid·rolloff·contrast·flatness·flux·zcr·rms·tempo) 추출(라벨 30곡, 곡당 ~4.4s) × 손라벨 4축 상관. 결과: **Timbre `contrast`×rough r=−0.815 PASS · Valence `mode`×valence r=+0.576 PASS**(합성 mode+centroid+harmonic R=0.595 미개선→mode 유지). **Arousal 탈락** — 전용 feature(LUFS·LRA·tempo_acf·VBL·rms변동) 전멸, **측정 템포 tempo_acf×지각tempo r=0.087(측정≠지각)**, 지각 energy/tempo는 스펙트럴 밝기(centroid·rolloff r≈0.6)가 잡으나 **contrast와 collinear(r≈0.52)라 독립 축 아님**. → **"실질 1.x차원" 확증**(contrast가 rough·energy·tempo·valence 4라벨 지배). **결정: x=timbre·y=valence 유지·변경없음, arousal 새 축 도입 안 함(전곡 추출 불요), Millsage·Ikka는 Phase A override가 최종**. 논문 `docs/research/emotion-axes-extraction.md`. 산출 `report/emotion-axes/`(phasec_features.csv 30·correlation.{txt,json}·screening.png). 도구 `phasec_{features,correlate,plot}.py`(--full로 전곡 추출 가능·진행/pause).
- **⏭ 남은 선택지(모두 optional)**: (a) 현 2축으로 확정 종료(권장·가장 정합) · (b) 전곡 660 정식 feature 부기(축 아님, 파생 보관용, ~46분) · (c) 라벨 확대 재검 · (d) 장르 밖 대조군. **Phase B(y 토글)는 B0·C 모두 arousal 부재라 보류/불요.**
- **데이터 보관(사용자 요청)**: 두 조사 데이터 폐기 금지 — B0 `cluster-energy-axis/onset_features.csv`(660)·C `emotion-axes/phasec_features.csv`(30) 커밋 보존, `audio_full`(660·15GB) 로컬 보존(gitignore). 전환성 progress/control JSON만 gitignore.
- **편집 규칙 동일**: `16-audiomap.js`·`desktop.css` 직접수정(리빌드 ✗) · `audio_map.json` 변경만 `python src/build.py`.

---

## 열린 결정 (사용자)
- ✅ ~~(레이아웃 — 묶어서 결정)~~ **해소(done 22)**: 유튜브 컬럼 하단 슬롯을 세로 분할 → **좌=음원맵 / 우=워드클라우드(대안 B)** + 유튜브 16:9 + 우패널 히스토그램·히트맵 동시표시 + 곡리스트 30%↓·긴곡명 마퀴 + 모바일 세로 스택.
- **(기능)** 진행률 링 70% 하드게이트: 현재 70% Green은 링 색상일 뿐, "70%↑만 최애밴드 자격" 게이트 미도입(현재는 스코어링 수축 `w(n)`만). 도입 여부 별도 결정(ux-02.md #2).

## 보류 · 백로그
- **(보류) 백필 1-c namedup 403**: 기존 곡 url을 Topic 음원으로 교체(품질 개선, 새 곡 아님). 후순위. (1-b 커버 135곡은 완료 — done 18.)
- **(보류) 진행도 Save/Load** (ux-02.md #4): 진행 json 백업/공유. ⚠️ Load = 기존 진행 덮어쓰기 → 손실 위험, 자동 백업·복구 경로 선설계 필수. 코멘트(`bandori-song-comments-v1`) 직렬화 포함 여부 확정 필요.
- **✅ (완료, done 24~25) 재생 이퀄라이저 = 음원맵 재생 펄스** — 전곡 660 pulse + **렌더 lazy-fetch** + **에너지 기반 동적 subdivision**(음량→박/8분, 글로벌 절대음량) + 볼륨 프리셋 4단계(곡 최대볼륨 상대화) + 광고펄스 버그수정. 상세 = **[report/emoi-cluster-pulse](report/emoi-cluster-pulse/README.md)**. 롤백 = `16-audiomap.js` `CL_PULSE_BPM=false`. **(보류)** 방안 B(구간 tempo period) 프로토타입만(`section_pulse_proto.py`) · mugendai/난곡 예외 큐레이션(`CL_ONSET_DEFDIV`). 원안 = [spec/equalizer-animation.md](spec/equalizer-animation.md).

---

## 참고 (TODO 아님)

### ⏪ 롤백 지점
`backup/main-20260630-emoicloud`(local·origin) = emoi-cloud(워드클라우드 색·품질) 머지 **직전 main = `cebbce4`**. 문제 시 `git reset --hard cebbce4`(+force-push) 또는 `git revert -m 1 961ab93 && git push origin main`(라이브 안전·권장). 이전 백업 `backup/main-20260630` = `d586ffb`(1-b 커버 머지 직전).

### 지역락 — 정책 확립 (done 15·16, 절차만 재사용)
- **감지**: `check_embeddable.py`(Data API `regionRestriction` + 한국 IP `playabilityStatus` 2신호). 신규 백필은 `new_songs.csv` 대상 동일 로직.
- **정책(2026-06-29)**: 지역락 = 앱 데이터(`songs/*.yaml`)에서 삭제, 곡 정보는 `invalid_url.csv` 보존(가드: 그 vid는 재실행으로 부활 안 함).
- **parked 4곡**(끝까지 지역락): poppin `千本桜` · RAS `DAYBREAK FRONTLINE`·`DEAD HEAT BEAT` · roselia `Our Carol`. (나머지 지역락 20곡은 대체 음원 재등록 완료 — done 19.) 워크시트 `region_blocked.csv`, 대체 URL은 **제목 대조 검증 필수**(세션 19 오입력 1건 적발).
