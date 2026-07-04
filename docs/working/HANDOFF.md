# HANDOFF: bandori-song-sorter — 남은 작업

**이 문서 = 앞으로 할 일의 인덱스.** 각 작업은 요약 + 상세 레퍼런스 링크로만 구성한다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 단일 출처는 memory `wordcloud_quality_plan.md`.

마지막 갱신: **2026-07-04(세션 23)** — **작업 2(음원맵 전곡 확대) 완결·동결**: 오디오 **659/660** 완주(`android_music` 클라이언트로 403 복구 — `tv/ios`는 DRM/PO토큰), `audio_map.json` **659곡/13밴드 + `norm` 파라미터 동결**(증분 append 선결), `build.py` 반영. + **재생 펄스 방안 A**(지각 pulse=ACF 옥타브비율, 파일럿 6/7) + **음원맵 HUD**(우주선 스타일)·연출·버그수정. 브랜치 `feature/emoi-cluster-v3b`(미머지·푸시됨). 상세 **done 23**.
> **⏭ 다음 = ① 머지(`v3b`→`feature/emoi-cluster`→`main`, 실검수 후) · ② 작업 3(자동화 파이프라인 — 동결 `norm` 기반 증분 append).** roselia `競宴Red×Violet` 1곡(DRM)은 증분으로.
이전: (2026-07-04) 재생 펄스 파일럿(beat 그리드+드럼 볼륨) → 세션 23에서 방안 A로 완성. (2026-07-03 17:00) 작업 1(D) 레이아웃 확정 + 정적파일 분할 main 머지(done 22).

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
| 3. 자동화 파이프라인 | 🔜 **본류**(2 완료 → 다음) | → [spec/pipeline-automation.md](spec/pipeline-automation.md) |
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

## 작업 3. 자동화 파이프라인 (RSS → cluster → main 반영)
RSS 수집 → cluster 분석 → 라이브 반영을 `actions/` 오케스트레이터 크론으로. **설계 = [spec/pipeline-automation.md](spec/pipeline-automation.md)** (착수 전 필독).
- 백로그의 **Phase 1.5(build+deploy 자동) + Phase 2(auto-merge)** 통합. Phase 1.5 = 가치·리스크 최선 → 1순위. 상세 done 13.
- **작업 2에 의존**: 전곡 빌드 + 정규화 파라미터 저장(§5)이 증분 반영의 선결.
- 오디오 = 로컬 벌크 + CI 소량 + fail-soft. CI는 이미 consent-wall로 length 스크랩 차단됨(`length_s=null`) = 다운로드 신뢰성 리스크 실증.
- (정리) 옛 프로토타입 untracked 잔재 `rss_seen.json`·`rss_inbox.csv`·`verify_cache.json` 삭제 가능.

---

## 열린 결정 (사용자)
- ✅ ~~(레이아웃 — 묶어서 결정)~~ **해소(done 22)**: 유튜브 컬럼 하단 슬롯을 세로 분할 → **좌=음원맵 / 우=워드클라우드(대안 B)** + 유튜브 16:9 + 우패널 히스토그램·히트맵 동시표시 + 곡리스트 30%↓·긴곡명 마퀴 + 모바일 세로 스택.
- **(기능)** 진행률 링 70% 하드게이트: 현재 70% Green은 링 색상일 뿐, "70%↑만 최애밴드 자격" 게이트 미도입(현재는 스코어링 수축 `w(n)`만). 도입 여부 별도 결정(ux-02.md #2).

## 보류 · 백로그
- **(보류) 백필 1-c namedup 403**: 기존 곡 url을 Topic 음원으로 교체(품질 개선, 새 곡 아님). 후순위. (1-b 커버 135곡은 완료 — done 18.)
- **(보류) 진행도 Save/Load** (ux-02.md #4): 진행 json 백업/공유. ⚠️ Load = 기존 진행 덮어쓰기 → 손실 위험, 자동 백업·복구 경로 선설계 필수. 코멘트(`bandori-song-comments-v1`) 직렬화 포함 여부 확정 필요.
- **(대체로 완료) 재생 이퀄라이저 = 음원맵 재생 펄스** — B안(lazy 사전계산). **방안 A(지각 pulse=ACF 옥타브비율) 구현·검증 완료**(파일럿 6/7, done 23) + 펄스 프리셋 3단계·색 가시성 보정·**박 고정 확정**. **남은 것**: 전곡 확대(`build_pulse_all.py` demucs CPU ~45s/곡 · onsets 대량 시 lazy fetch 전환) · mugendai 난곡 큐레이션. 상세 = **[report/emoi-cluster-pulse](report/emoi-cluster-pulse/README.md)**. 롤백 = `16-audiomap.js` `CL_PULSE_BPM=false`. 원안 = [spec/equalizer-animation.md](spec/equalizer-animation.md).

---

## 참고 (TODO 아님)

### ⏪ 롤백 지점
`backup/main-20260630-emoicloud`(local·origin) = emoi-cloud(워드클라우드 색·품질) 머지 **직전 main = `cebbce4`**. 문제 시 `git reset --hard cebbce4`(+force-push) 또는 `git revert -m 1 961ab93 && git push origin main`(라이브 안전·권장). 이전 백업 `backup/main-20260630` = `d586ffb`(1-b 커버 머지 직전).

### 지역락 — 정책 확립 (done 15·16, 절차만 재사용)
- **감지**: `check_embeddable.py`(Data API `regionRestriction` + 한국 IP `playabilityStatus` 2신호). 신규 백필은 `new_songs.csv` 대상 동일 로직.
- **정책(2026-06-29)**: 지역락 = 앱 데이터(`songs/*.yaml`)에서 삭제, 곡 정보는 `invalid_url.csv` 보존(가드: 그 vid는 재실행으로 부활 안 함).
- **parked 4곡**(끝까지 지역락): poppin `千本桜` · RAS `DAYBREAK FRONTLINE`·`DEAD HEAT BEAT` · roselia `Our Carol`. (나머지 지역락 20곡은 대체 음원 재등록 완료 — done 19.) 워크시트 `region_blocked.csv`, 대체 URL은 **제목 대조 검증 필수**(세션 19 오입력 1건 적발).
