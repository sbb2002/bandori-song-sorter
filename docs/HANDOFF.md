# HANDOFF: bandori-song-sorter — 남은 작업

이 문서는 **앞으로 할 일만** 담습니다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 진행의 단일 출처는 memory `wordcloud_quality_plan.md`.

마지막 갱신: **2026-07-01** — #1 워드클라우드 완료(세션 20, main 머지) · **#2 클러스터: 키워드→음원 피벗 + v2 UI 완료**(feature/emoi-cluster-v2, 미머지). 옵션1 밴드 음원 지도/옵션2 CLAP비교→librosa채택/옵션3 CLAP 유사곡 탐색기 + **v2: 음원맵을 유튜브 하단 상시영역으로 이동·축 의미 라벨·밴드 원 클릭 강조**. 남음=브라우저 실검수·분할비율·밴드정보 이동 결정. 실험 종합 = `docs/report/cluster_experiment.md`. #1은 (D) 배치만.

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
| 2 | 클러스터(키워드→**음원** 피벗) + v2 UI | 중~높 | ✅ 옵션1·2·3 + v2(유튜브 하단 이동·축라벨·밴드클릭) 구현(feature/emoi-cluster-v2, 미머지) — 브라우저 실검수·분할비율·밴드정보 이동 남음 |
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

## 2. 클러스터 — **키워드→음원 피벗 완료** (옵션 1·2·3 구현, 미머지)

> ⚠️ **방향 전면 변경**(2026-07-01). 키워드/문장/곡 어느 단위로도 **가사로는 밴드 군집 불가**(silhouette≈0). **음원 음악특징으로 밴드 단위 집계 시 밴드 구별됨**(LOO 분류 59%). **종합 실험 기록 = [docs/report/cluster_experiment.md](report/cluster_experiment.md)**(전 단계 수치·방법·결정), 백엔드 비교 = [report/cluster_audio_clap.md](report/cluster_audio_clap.md) + `cluster_audio_backends.png`. 구 키워드 파이프라인(`build_embeddings.py`·`keywords_2d.json`)은 **미사용 잔존**(폐기 가능).

- **파이프라인**: `python tools/cluster/build_audio_map.py`(= `--backend librosa --sim clap`) → `cluster/audio_map.json`(커밋). 입력 `cluster/songs_top10.csv`(TOP10×10 매니페스트, 커밋). 음원은 `data/*.yaml` url에서 **yt-dlp로 60초·48kHz 추출 → `cluster/audio_cache/`(gitignore, 저작물)**. 의존성 `tools/cluster/requirements-audio.txt` + `transformers>=5`(CLAP 내장). **로컬 빌드 전용(CI 불가)**, 산출 JSON만 커밋. 재생성 후 `python build.py`.
- **좌표·지표**: 밴드 중심점에 PCA(2) fit → 곡·중심 한 좌표계. **원점(0,0)=곡 평균('평균적 소리'), 95퍼센타일 스케일+±60 클립(뭉침 완화)**. `audio_map.json` = `{axes:{x,y:{feature,pos,neg,r}}, songs:[{band,song,x,y,sim:[…]}], centroids:[{band,x,y,n}], metrics:{loo_acc,…}}`. `sim`=곡별 **CLAP 코사인** 유사곡 인덱스. `axes`=각 축이 어떤 음향특징과 상관되는지(현재 x=rolloff 고음↔저음, y=zcr 매끄↔거침; `AXIS_FEATURES` 상관분석).
- **렌더(v2)**: `script.js` `renderCluster`/`_clDraw`/`_clSimList`/`_clAxisLabels`(ECharts) — 작은 점=곡, 큰 라벨 점=밴드 중심. **곡 클릭=CLAP 유사곡 연결선·강조 / 밴드 원 클릭=그 밴드 곡 전체 강조 / 빈영역=해제**. 원점 십자 점선(markLine), 4모서리 축 의미 라벨(`#cl-ax-*`), `#cl-similar` 목록. 줌/팬. **유튜브 컬럼 하단에 상시 표시**(`.audiomap-area`, 우패널 탭에서 분리 — v2).
- **역할 분담(실측 결론)**: 밴드 **식별 지도**=librosa(LOO 59% > CLAP 45%), 곡 **유사곡**=CLAP(무드 일관 > librosa 지문매칭). 융합은 손해. 상세 report.

### 🔜 다음 세션 할 일 (feature/emoi-cluster-v2, 미머지)
1. **브라우저 실검수**: `python -m http.server` → 유튜브 하단 음원맵. 축 라벨·원점·**밴드 원 클릭→그 밴드 곡 전체**·곡 클릭→유사곡, 모바일(음원맵 320px). node 미설치라 `npm test`·실렌더 미확인.
2. **분할 비율 결정**(yt:음원맵, 현재 50:50) — 사용자 보류.
3. **밴드 정보(워드클라우드)도 이쪽으로 옮길지** — 사용자 보류(가독성 보고 결정). 옮기면 우패널은 히스토/히트맵만.
4. **머지 경로**: `feature/emoi-cluster-v2` → `feature/emoi-cluster` → `main`(또는 직접). 라이브는 sbb2002.github.io.
5. (선택) 밴드 아이콘 배지 · 청크(10s)평균 CLAP·전곡 검증(report §9) · 구 `keywords_2d.json`/`build_embeddings.py` 폐기.

### 한계
2D 투영은 정성용(정직성 지표는 고차원 LOO). 표본 밴드별 ~9곡(TOP10−지역락/실패), 60초 1구간. 동일 장르(BanG Dream)라 식별 난도 본질적으로 높음(silhouette≈0이 그 증거).

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
