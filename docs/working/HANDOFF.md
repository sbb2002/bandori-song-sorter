# HANDOFF: bandori-song-sorter — 남은 작업

**이 문서 = 앞으로 할 일의 인덱스.** 각 작업은 요약 + 상세 레퍼런스 링크로만 구성한다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 단일 출처는 memory `wordcloud_quality_plan.md`.

마지막 갱신: **2026-07-06(세션 26)** — **작업 3 = CI 다운로드 봇월 확정 → 반자동 전환**: E2E dry-run 3회로 GitHub Actions(데이터센터 IP)에서 YouTube 다운로드가 봇월에 막힘 실증(기본·클라이언트 로테이션·PO토큰 전부 hard-block). 벽은 IP 평판 → 클라우드로는 불가. **다운로드만 레지덴셜(집) IP로 빼는 반자동 채택**: (1)Actions가 매일 감지+Telegram 알림 (2)로컬에서 원커맨드로 다운로드~main push→deploy 자동. 계획 = `~/.claude/plans/floofy-tickling-corbato.md`. **현재 = 구현 중**(작업 브랜치 `feature/new-song-semiauto`).
> **⏭ 다음 = 작업 3 구현·검증(§ 작업 3):** pipeline.yml 재작성(감지+알림) + `src/tools/pipeline/run_local.py`·`notify.py` + orchestrate `--notify`. 검증 = 로컬 다운로드 실증(CI ✗였던 곡이 로컬 ✅).
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
| 3. 자동화 파이프라인 | 🔧 **반자동 전환·구현 중**(CI 다운로드 봇월 확정 → Actions 감지·알림 + 로컬 처리) | § 작업 3 · [spec](spec/pipeline-automation.md) |
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

## 작업 3. 자동화 파이프라인 — 신곡 로더 (🔧 반자동 전환 · 구현 중)
**상세 구현·배선 = [done.md](done.md) 세션 26.** 설계 = [spec/pipeline-automation.md](spec/pipeline-automation.md). 작업 2(전곡 빌드+`norm` 동결)에 의존 — 완료됨.

### ⛔ 결론 — CI 다운로드는 봇월로 불가(실증 확정, 2026-07-06)
E2E dry-run으로 CI 오디오 다운로드를 검증한 결과 **GitHub Actions(데이터센터 IP)에서 YouTube 다운로드가 봇월("Sign in to confirm you're not a bot")에 막힘**이 확정:
- run `28789165878` 기본(android vr) hard-block → run `28789906761` **클라이언트 로테이션**(tv,web_safari,ios) 전부 hard-block → run `28791454189` **PO 토큰**(bgutil provider, 익명 visitor) web_safari/tv/mweb 전부 hard-block.
- 벽은 **클라이언트가 아니라 IP 평판**. spec §4 카드 ①(최신 yt-dlp)·②(로테이션)·PO토큰까지 소진. Render 등 다른 클라우드도 전부 데이터센터 IP라 동일(도망 불가).
- ★단 **다운로드 이후(demucs·pulse·좌표·커밋·배포)는 네트워크 게이트 없음** → E2E가 다운로드 直前까지 전 스텝 green으로 실증. **다운로드만 레지덴셜(집) IP로 빼면 나머지는 100% 자동.** 집 IP 다운로드는 전곡 660 벌크로 이미 실증.

### 🔧 채택 아키텍처 — 반자동(Actions 감지·알림 + 로컬 원커맨드 처리)
계획 원본 = `~/.claude/plans/floofy-tickling-corbato.md`. 흐름:
1. **(Actions, 매일 23:00 KST = cron `0 14 * * *`)** `orchestrate.py --detect-only --notify` → 신곡 있으면 **미처리 신곡 전체를 요약한 Telegram 메시지 1건** 전송(다운로드 안 함).
2. **(Local, 사용자 트리거)** 알림 받고 **명령어 한 줄** → 다운로드(집 IP)→demucs/pulse→좌표 append→`push origin main` → `deploy.yml` 자동 배포.

**격리 원칙**: 자동화 git 활동(main 커밋·푸시)이 데브 핫픽스와 안 얽히도록 **전용 로컬 클론에서만 실행**(별개 브랜치로는 워킹트리 공유라 격리 안 됨 / 별도 GitHub 레포는 과함 — 데이터는 이 레포로 push돼야 deploy됨). 코드는 `src/tools/pipeline/`에 두어 버전관리.

### 컴포넌트
- `.github/workflows/pipeline.yml` — **감지+알림 전용으로 재작성**(오디오/PO/node 스텝 제거, cron 23:00 KST). `TELEGRAM_BOT_TOKEN`·`TELEGRAM_CHAT_ID` secrets.
- `src/tools/pipeline/run_local.py`(신규) — 사용자 원커맨드. 전용 클론(기본 `../bandori-pipeline`)을 `origin/main`로 reset → cwd=클론에서 `actions/orchestrate.py` 실행. 인자 `--repo-path/--limit/--dry/--test-band/--test-video`.
- `src/tools/pipeline/notify.py`(신규) — `send_telegram()`(urllib, 무의존). Actions·로컬 공용.
- `actions/orchestrate.py` — `--notify`/`--notify-test`만 신설. process_song·commit_and_push·`--test-*`는 **무수정 재사용**(로컬 엔진).
- `deploy.yml` **무변경**(로컬 push가 트리거).

### 로컬 사용법
```
python src/tools/pipeline/run_local.py                       # 감지→다운로드~push (실제 반영)
python src/tools/pipeline/run_local.py --test-band afterglow --test-video 09B-WljIiTo  # E2E 검증(dry)
```
사전조건: 오디오 스택 env(yt-dlp·node·torch/demucs·librosa·ffmpeg, 이 장치는 base miniconda에 전부 있음) + git push 자격.

### Telegram 명령 봇 (라이브)
상시 서버 없이 Telegram 명령을 **Actions 5분 폴링**(`telegram-bot.yml` cron `*/5`, public 레포=무료)으로 처리. `src/tools/pipeline/telegram_bot.py`가 `getUpdates`+ack(무상태)·**인가 chat_id만**. 응답 지연 ~5~15분(GitHub 크론 best-effort).
- `/help` · `/detect`(감지 수동+결과·예외 응답) · `/status`(주기·상태) · `/pause` · `/resume`.
- 일시정지 = `actions/bot_state.json {paused}`(deploy 경로 밖, 봇이 [skip ci] 커밋). `pipeline.yml`이 읽어 paused면 감지·알림 skip. `/pause`는 **일일 감지만** 멈춤(봇 폴러는 계속 = `/resume` 수신).
- 브릿지는 **폴링 채택**(웹훅+Cloudflare Worker 대안은 즉시 응답이나 인프라+1). 즉시 실행 = `gh workflow run telegram-bot.yml`.

### 상태 — ✅ 반자동 + 봇 완료·라이브
- ✅ 구현·머지: pipeline.yml(감지+알림) · run_local.py · notify.py · orchestrate `--notify` · telegram_bot.py (main).
- ✅ 검증: 로컬 다운로드 실증(CI ✗ 곡이 로컬 ✅) · 데브 레포 격리 · Telegram 알림/명령 전송(run 28796418124·28798948000).
- ✅ secrets `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` 등록.

### 남은 것 (선택·후순위)
- DRM `roselia 競宴Red×Violet`: yt-dlp 취득 불가 → fail-soft 스킵(수동).
- (선택) 영구실패 재시도 상한 가드 · index.html `git rm --cached`(Option A 완전화) · 옛 프로토타입 잔재(`rss_seen.json`·`rss_inbox.csv`·`verify_cache.json`) 삭제.
- (미검증) `/pause`·`/resume`의 상태 커밋 경로(bot_state.json push) — 실사용 시 확인.
- (사용자 코멘트) 다운로드 이후 분석 및 데이터 푸쉬 작업을 진행하는 별도의 파일도 필요함. 왜냐하면 일부 로컬에서 분석 라이브러리를 구동할 환경이 안될 수도 있기 때문임. 현재 만든 파일도 유지할 것.

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
