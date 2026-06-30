# HANDOFF: bandori-song-sorter — 남은 작업

이 문서는 **앞으로 할 일만** 담습니다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 진행의 단일 출처는 memory `wordcloud_quality_plan.md`.

마지막 갱신: **2026-06-30** — 워드클라우드 품질 2-c(A·B·C) + 키워드 밴드 퍼스널 컬러·mutype 투톤·네온 글로우 완료(done 세션 20, feature/emoi-cloud → main 머지). #1은 (D) 배치만 남음.

> 🖥️ **다음 작업은 다른 로컬·다른 세션에서 진행** — 시작 전 체크:
> 1. `git pull origin main`(emoi-cloud 머지 반영 · 660곡). 작업은 **새 feature 브랜치**에서 시작.
> 2. `.env`의 `YOUTUBE_API_KEY`는 **장치별·비커밋**(.gitignore) — 백필/지역락 점검 시 재추가 필요(없으면 `insert_backfill.py`·`check_embeddable.py` 즉시 중단).
> 3. `npm test`(=`node --test`)용 **node 설치 확인** — 직전 장치엔 없어 미실행했음.
> 4. 워드클라우드 가사 원문 `assets/lyrics/<band>.md`는 **로컬 전용(gitignore)** — 커밋된 `wordcloud/<band>.yaml`로 2-c 검수·렌더는 가능하나, `build_keywords.py` **재생성은 원문 .md 필요**(새 장치엔 없음 → 가사 재공급 or 기존 yaml만 편집).
> 5. 로컬 브랜치(2026-06-30 정리 후): `main` + 백업 3(`backup/main-20260620·22·30`) + `feature/ux-02-opt-a`(옵션A 유일본, 미머지·원격없음 — 삭제 금지).

---

## 현황

- 데이터 **677 트랙 / 화면 660곡(dedup) / 13밴드**. 워드클라우드 **라이브**(품질 2-c A·B·C + 밴드 퍼스널 컬러·mutype 투톤·네온 글로우 완료, done 세션 20).
- 백필 오리지널(1-a)·커버(1-b)·지역락 처리 **완료**(done 세션 14~19). 화면 곡수 526→**660**(+134). 끝까지 KR 지역락인 4곡만 제외.
- 다음 본류: **#1은 (D) 배치 결정만 남음 → #2 키워드 2D 클러스터.**

> ⏪ **롤백 지점 — `backup/main-20260630-emoicloud`** (local·origin) = emoi-cloud(워드클라우드 색·품질) 머지 **직전 main = `cebbce4`**. 문제 시 `git reset --hard cebbce4`(+force-push) 또는 `git revert -m 1 961ab93 && git push origin main`(라이브 안전·권장). (이전 백업 `backup/main-20260630`=`d586ffb`는 1-b 커버 머지 직전.)

---

## 우선순위

| 순 | 작업 | 난이도 | 상태 |
|----|------|--------|------|
| 1 | 워드클라우드 품질 (2-c) A·B·C + 색상 | 중 | ✅ 완료(세션 20) — (D) 배치만 남음 |
| 2 | 키워드 의미공간 2D 클러스터 | 중~높 | ⬜ 미착수 (1의 키워드·퍼스널컬러 재활용) |
| — | (보류) 백필 1-c namedup 403 | — | url 품질 개선 · 후순위 |
| — | (보류) 진행도 Save/Load | 중~높 | 리스크 높음(덮어쓰기) |
| — | (백로그) youtube_rss Phase 2 / Phase 1.5 | — | precision 축적 후 |

원칙: **밴드 시각화 마무리(1) → 후속 확장(2)**. 보류·백로그는 별도 결정 사안.

---

## 1. 워드클라우드 품질 보완 (2-c) — (D) 배치만 남음

파이프라인·렌더·TF-IDF·음차화·감성 데이터·라이브 머지(done 17), **A·B·C 검수 + 키워드 색상(done 20) 완료**. yaml 재생성 = `python tools/wordcloud/build_keywords.py`(가사 원문 `<band>.md` 필요) → `python build.py`. 단 yaml의 `ko`는 사용자 수동 검수본이라 재생성 시 덮어써짐(가사 있을 때만 재생성).

- ✅ **(A) ko 검수 / (C) 노이즈·외래어** (done 20): 전 밴드 yaml align N:1 오역 교정(熊 코끼리→곰 등), 보컬리제·단편 **줄 삭제**, 외래어 음차 표준화, 통일규칙(輝き→빛남·笑顔→미소·思い→생각·無限→무한·道程→여정). `build_keywords.py` OVERRIDE/STOPWORDS 확장(재생성 대비). ⚠️ **`weight:0`은 렌더에서 `|| 1`로 살아나므로 큐레이션 제거는 yaml 줄 삭제로 해야 함.**
- ✅ **(B) 가독성** (done 20): 표시 60→40, 폰트 하한(h/15)·`gridSize`(w/48) 여백 상향.
- ✅ **키워드 색상** (done 20): `script.js` `BAND_COLORS`(퍼스널 컬러 hue 고정) + 빈도 명도변주 35~82%, `BAND_SUBCOLORS` mutype 투톤 그라데이션(#2288dd, 글자 아래 ~22%), 폰트 분포 **Q2(중앙값)↑ 같은 색 네온 글로우**(shadowBlur 8). ALL 탭은 6색 팔레트(`WC_PALETTE`) 유지.
- ⬜ **(D) 배치 재결정** ⚠️ **사용자 결정 필요**: 우패널 탭이 좁아 워드클라우드에 부적합. 후보 = 유튜브 프레임 가로 2분할(아래=클라우드) / 전용 모달 / 하단 넓은 영역. #2 클러스터 게시위치(아래 2번)와 함께 결정.

> 참고: 가사 파일 규칙 — 빈 템플릿 `assets/lyrics/<band>_template.md`만 커밋, 채운 `<band>.md`는 `.gitignore`(가사 비커밋). 다른 세션은 `git pull`로 템플릿만 받고 `.env`(`YOUTUBE_API_KEY`)는 별도. 상세 done 세션 17.

---

## 2. 키워드 의미공간 2D 클러스터 (전 밴드 1장, global) — 미착수

1번 워드클라우드의 **키워드를 재활용** → **고유 키워드=점**, 다국어 단어 임베딩을 2D 투영(UMAP) 산점도. 오디오/BPM 불필요.

- **단위 = 고유 키워드 1개당 점 1개.** 그 점에 쓴 밴드 아이콘을 미니 배지로 표시(공유어=다중 아이콘=어휘 교집합 / 단일밴드어=개성). 점 크기 = 전체 빈도.
- **라벨 겹침**: 빈도 상위 N개만 상시 라벨 + 충돌회피, 나머지는 호버·줌 시 노출.
- **호버 UX**: 점 호버 → 툴팁(키워드·쓰는 밴드·밴드별 빈도). 밴드 아이콘 호버 → 그 밴드 키워드만 하이라이트(나머지 디밍).
- **감성/무드 축**: done 세션 17에서 보존한 감성 데이터(긍↔부정) + 진지성(진지↔유쾌) 다차원 벡터를 색·축으로 활용 가능.
- **게시 위치(고려중)**: 유튜브 프레임 가로 2분할(위=플레이어, 아래=클러스터) — 1번 D와 함께 결정 / 대안: 전용 모달, 우패널 탭. ⚠️ 모바일 레이아웃 검토.
- **렌더(안)**: 호버·줌·아이콘 symbol 필요 → ECharts scatter 유력.
- **한계**: 2D 투영은 거리 왜곡 있어 정성 해석용. 표본은 TOP10 가사 한정.

**밴드 퍼스널 컬러**(✅ 워드클라우드 적용 완료 — `script.js` `BAND_COLORS`/`BAND_SUBCOLORS`; #2 클러스터에도 재사용):

| 밴드 | 색 | 밴드 | 색 |
|------|------|------|------|
| poppin_party | `#ff3377` | morfonica | `#33AAFF` |
| afterglow | `#ee3344` | raise_a_suilen | `#33CCCC` |
| pastel_palettes | `#33ddaa` | mygo | `#0088BB` |
| roselia | `#3344aa` | ave_mujica | `#881144` |
| hello_happy_world | `#ffdd00` | mugendai_mutype | `#ff7788` (+보조 `#2288dd` 20% 그라데이션) |
| millsage | `#AA22EE` | ikka_dump_rock | `#FFAA33` |

---

## 보류 · 백로그

### (보류) 백필 1-c namedup 403
- **1-c namedup 403**: 기존 곡의 url을 Topic 음원으로 교체하는 품질 개선(새 곡 아님). 후순위.
- (✅ **1-b 커버 135곡은 완료** — done 세션 18: `insert_backfill.py --cover`로 135 삽입 − KR 지역락 21 제거 = **+114**.)

### (보류) 진행도 Save/Load (ux-02.md #4) — 리스크 높음
내 진행을 json 백업/공유. Load 시 Mine/Others 선택. ⚠️ **Load = 기존 진행 덮어쓰기 → 손실 위험.** 로드 전 자동 백업·복구 경로 선설계 필수. 디씨 첨부가 헤비/금기면 반려 가능.
- 직렬화 범위에 코멘트(`bandori-song-comments-v1`)를 `ranks`와 함께 포함할지 확정 필요.

### (백로그) youtube_rss 자동화 후속
- **Phase 2**(고신뢰 auto-merge) · **Phase 1.5**(build+deploy 자동): precision 축적 후 검토. 상세 done 세션 13.
- CI에선 길이 스크랩 막힘(`length_s=null`, consent wall) → 길이필터 비활성·`variant_tag`만 작동. `verify_links` oEmbed/길이 로직과 공유해 보강 가능.
- `tools/rss_seen.json`·`tools/rss_inbox.csv`·`tools/verify_cache.json`(옛 프로토타입 untracked 잔재) 삭제 가능.

---

## 열린 결정

- **진행률 링 70% 하드게이트**(done 세션 11): 70% Green은 **링 색상일 뿐**, "70%↑만 최애밴드 자격" 하드게이트는 미도입. 현 최애밴드는 스코어링 수축(`w(n)`)으로만 선정. 게이트 도입 여부는 별도 결정(ux-02.md #2 "최애밴드 표시 자격").
- **워드클라우드 배치**(1-D): 사용자 결정 필요.

---

## 지역락 — 정책 확립됨 (TODO 아님, 참고)

감지·정책 모두 해결됨(done 세션 15·16). 신규 검수 시 절차만 재사용:
- **감지**: `tools/curate/check_embeddable.py`(Data API `regionRestriction` + 한국 IP `playabilityStatus` 2신호). 신규 백필은 `tools/collect/new_songs.csv` 대상으로 동일 로직 재사용.
- **정책(2026-06-29)**: 지역락 = 법적 이슈·대체 불가 → 앱 데이터(`data/*.yaml`)에서 삭제, 곡 정보는 `tools/curate/invalid_url.csv`에 보존(가드: 그 vid는 재실행으로 부활 안 함).
- **최종 parked 4곡**(`invalid_url.csv` modified_url 공란 = 끝까지 지역락): poppin `千本桜` · RAS `DAYBREAK FRONTLINE`·`DEAD HEAT BEAT` · roselia `Our Carol`. (나머지 지역락 20곡은 사용자가 찾은 대체 음원으로 재등록 완료 — done 세션 19.)
- 🔎 **`tools/curate/region_blocked.csv`** = 위 4곡 기록 워크시트. 대체 음원 찾으면 `url` 칸 채워 `insert_backfill.py --cover`로 재등록(블락 vid는 invalid_url.csv 가드로 충돌 없음). ⚠️ 대체 URL은 **제목 대조 검증 필수**(세션 19에서 곡 오입력 1건 적발).
