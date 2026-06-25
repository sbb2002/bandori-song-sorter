# HANDOFF: bandori-song-sorter — 남은 작업

해야 할 것·남은 것만 담습니다. **완료된 작업 기록은 [done.md](done.md)** 참조.
(참고 사실 — v2 표시 범위, 라이브/원격 URL, 환경 등 — 도 done.md 상단에 정리.)

마지막 갱신: **HANDOFF 1 진행중** — Data API 조회수→밴드별 TOP10 + 가사 템플릿(`assets/lyrics/`) 완료, 백필 후보 도출 완료(신규 165 = 오리지널 30 / 커버 135 · namedup 402). 남은 건 **오리지널 30개 데이터 추가**(1-a) 등. 도구: `tools/youtube_api.py`·`band_top10.py`·`backfill.py`. (2026-06-25)

> 이전 갱신: idea/260625.md 검토 완료 → 채택 3건 이관, 자동 장르추출 등 반려. 메타패널 '밴드 중심' 전환(밴드소개 + 밴드 워드클라우드), 워드클라우드는 밴드별 조회수 TOP10 가사(사용자 직접 제공·원문 미보관).

> **ux-02.md 1·2·3·6·7번 + youtube_rss 자동화 + 데이터 정합성 검수 완료**. 상세는 [done.md](done.md). 옵션 A(랭크순)는 `feature/ux-02-opt-a` 백업, 진행률 링 conic 시안은 `feature/ux-02-ring-conic` 백업.

---

## 작업 순서 (의존성·우선순위)

| 순 | 작업 | 난이도 | 비고 |
|----|------|--------|------|
| 1 | YouTube Data API — 조회수 TOP10 + 미추가 곡 백필 | 중 | 🔄 조회수/백필 완료 · **오리지널 30 추가 남음** |
| 2 | 밴드 메타패널(우패널 3번째 탭): 밴드소개 + 밴드 워드클라우드 | 중 | 1의 조회수 TOP10 + 사용자 제공 가사 필요 |
| 3 | (후속) 곡 가사 의미공간 2D 클러스터 | 중~높 | 2의 가사 재활용 · 가사 확보 후 채택 판단 |
| — | (보류) 진행도 Save/Load | 중~높 | 리스크 높음(진행 덮어쓰기) |
| — | (보류) 한국 지역락 대응 | 높(불확실) | 감지·대체 방안 미정 |

원칙: **데이터 기반(1) → 밴드 시각화(2) → 후속 확장(3)**. 보류 2건은 별도 결정 사안.

---

### 1. YouTube Data API — 조회수 TOP10 + 미추가 곡 백필 (new_idea #3) — 🔄 진행중
키: `.env`의 `YOUTUBE_API_KEY`(stdlib 파싱 — `tools/youtube_api.py`의 `load_env_key`). `.gitignore`에 `.env` 포함. youtube_rss의 'no API key'(CI RSS)와 **별개** — 일회성/저빈도 조회 전용. `backfill.py`는 출력 전용·멱등이라 재실행 안전.

**✅ 완료**
- `tools/youtube_api.py` — Data API v3 stdlib 클라이언트: `load_env_key` / `fetch_view_counts`(videos.list) / `fetch_uploads`(channels+playlistItems 페이징).
- `tools/band_top10.py` — 재생가능 트랙 조회수 → 밴드별 TOP10. 커버 제외(`--no-cover`), 같은 video_id dedup(roselia LOUDER 중복 방어).
  → **10개 밴드 TOP10 확정**, `assets/lyrics/<band>.md` 가사 템플릿 생성(gitignore·원문 비커밋). 조회수 443/443 수신.
- `tools/backfill.py` — Topic 업로드 전체 vs known(id/name) 비교 → 누락 후보 **출력만**(데이터 미변경). variant/known_name 필터는 youtube_rss와 동일.
  → 결과: **신규 165 = 오리지널 30 + 커버 135 · namedup 402**.
    · 오리지널 30(스팟체크로 진짜 누락 확인): roselia 14, raise_a_suilen 7, poppin_party 5, morfonica 2, afterglow 1, ave_mujica 1. **2022년 정규앨범 곡 포함**(roselia Our Carol/Swear, raise DEAD HEAT BEAT) — RSS로 못 잡던 것.
    · namedup 402 = 음원우선 정책으로 데이터가 Topic 외 영상(MV 등)을 url로 씀 → **신곡 아님**(url 품질 영역).

**⬜ 남은 것**
- **(1-a) 오리지널 30개 데이터 추가** ← 다음 작업. `python tools/backfill.py`로 후보 재산출(멱등) → `insert_track` 기반 추가 스크립트(dry-run → loss-0 검증 → `--apply`). 오리지널은 New Singles(numbering=`Single`/album=`New Singles`), track_number=published, img=FALLBACK_IMG.
  - ⚠️ poppin `(Popipa Acoustic Ver.)`·`(Poppin'Party Ver.)`·`Yes! BanG Dream! (Acoustic Ver.)` 등 **편곡/버전곡은 취사선택**(같은 곡 다른 편곡).
- **(1-b) 커버 135개**: Covers 카탈로그 확장(numbering=`Cover`/album=`Covers`). 양 많아 **별도 배치로 보류**(사용자 보류 동의 대기). 이게 new_idea #3의 'A(Topic 백필)'에 해당. 그래도 빠지는 '유튜브 한정 커버'는 B(공식채널 バンドリちゃんねる☆ 수집)인데 노이즈·밴드배정 난점 → 후순위.
- **(1-c) namedup 402**: url을 Topic 음원으로 교체하는 url 품질 개선 — 별도·후순위.
- 대상 밴드: Topic 채널 보유 12밴드. various_artists(Topic 없음)·ikka_dumb_rock·millsage(업로드 1개)는 사실상 제외.

### 2. 밴드 메타패널 + 밴드 워드클라우드 (new_idea #1, '밴드 중심'으로 전환)
위치: **우패널 3번째 탭** `[밴드 정보 | 히스토그램 | 히트맵]`. **그리드 미변경**(리스크 최소). 곡 클릭 시 밴드정보 탭 자동 활성화. 가독성 나쁘면 롤백 → 원안(유튜브 프레임 가로분할).
- **곡 단위 메타(곡 길이·곡 장르·수록 자켓)는 반려** — 수집/관리 부담. 메타패널은 밴드 정보로 한정.
- **밴드소개**: 공식 소개문/플레이버 텍스트(읽는 글).
- **밴드 워드클라우드**: 밴드별 조회수 TOP10 곡 가사 → 키워드 빈도 → 밴드 개성/테마 시각화.
  - **가사는 사용자가 직접 복붙 제공**(크롤링 안 함 → 수집 저작권 회피). **원문 미보관** — 빌드타임에 키워드/빈도 json만 산출하고 원문 삭제.
  - 처리 2안(착수 시 택1): ① 한국어 번안 가사 제공, ② 일어 원문 명사 추출 → 한국어 번역 후 렌더. 형태소 분석(fugashi 등)·렌더 라이브러리(wordcloud2.js 등)는 착수 시 결정.
- **현재 상태**: 1번에서 `assets/lyrics/<band>.md` 가사 템플릿(10밴드 TOP10) 생성 완료 → **사용자가 가사 채우는 중**. 채워지면 형태소→빈도 json(원문 삭제)→렌더 착수. mygo `春日影`는 2버전이 들어있으나 가사 동일하니 1개만 채울 것.

### 3. (후속) 곡 가사 의미공간 2D 클러스터 (new_idea #2 대안)
2번 TOP10 가사를 **재활용** → 가사 임베딩(다국어 문장 임베딩) 2D 투영(UMAP/PCA) 산점도. **오디오/BPM 불필요**.
- 보여줄 것: 곡 간 의미 거리 · 밴드별 응집/분산도 · **밴드 내 이단아 곡(예: Roselia 락발라드)** · 밴드 간 겹침·대비 · 주제 군집.
- 한계: 가사 있는 **~100곡(10밴드×10)만**. 조회수 TOP10 밖 묻힌 곡은 미표본. 2D 투영은 거리 왜곡 있어 **정성 해석용**.
- 워드클라우드용 가사가 모이면 **실제 분포를 보고 채택 판단**.

---

> ⚠️ **진행률 링(done 세션 11)에서 보류된 열린 결정**: 70% Green은 **링 색상일 뿐**이고, "70% 이상만 최애밴드 표시 자격" **하드게이트는 미도입**. 현 최애밴드는 스코어링 수축(`w(n)`)으로만 선정. 게이트 도입 여부는 별도 결정 사안(ux-02.md #2 "최애밴드 표시 자격 조건"과 연결).

> ℹ️ **youtube_rss 자동화 운영 메모**: ① CI에선 길이 스크랩이 막혀(`length_s=null`, 데이터센터 IP consent wall) **길이필터 비활성·`variant_tag`만 작동** → 데이터 정합성 검수(done 세션 14)의 `verify_links` oEmbed/길이 로직과 공유해 보강 가능. ② `tools/rss_seen.json`(폐기 프로토타입 산출물) untracked 잔존 → 삭제 가능. ③ Phase 2(고신뢰 auto-merge)·Phase 1.5(build+deploy 자동)는 precision 축적 후 검토. 상세는 done.md 세션 13.

---

### (보류) 진행도 Save/Load (ux-02.md #4) — 난이도 중~높 · 리스크 높음
내 진행상황을 **json으로 백업/공유**. Load 시 즉시 로딩 아니라 **Mine/Others 선택**(Mine=내 것 즉시 로드, Others=타인 것 로드 대화창). 내 진행은 항상 백업. 공유는 디씨 등 커뮤니티 첨부 상정.
- ⚠️ **Load = 기존 진행 덮어쓰기 → 데이터 손실 위험**. 로드 전 현재 진행 자동 백업·복구 경로 선설계 필수.
- 후순위: 디씨 json 첨부가 금기/헤비하면 반려 가능. (코멘트는 별도 키 `bandori-song-comments-v1`로 구현됨 → Save/Load 직렬화 범위에 `ranks`와 함께 코멘트 포함 여부 확정 필요.)

### (보류) 한국 지역락 노래 대응 (ux-02.md #5) — 난이도 높(불확실) · 리스크 중
일부 곡이 한국 지역락일 수 있음 → 대응책 필요.
- 미정: 지역락 **감지 방법**(클라이언트 판별 난해), **대체 링크/표기** 정책. 방안 구상부터 필요. `verify_links` oEmbed 점검 로직 일부 공유 가능.
