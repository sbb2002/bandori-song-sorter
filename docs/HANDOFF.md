# HANDOFF: bandori-song-sorter — 남은 작업

이 문서는 **앞으로 할 일만** 담습니다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 진행의 단일 출처는 memory `wordcloud_quality_plan.md`.

마지막 갱신: **2026-06-30** — 백필 1-b 커버 + 지역락 대체 재등록(done 세션 18·19, 화면 660곡) · handoff 재작성(완료분 done 17 이관).

---

## 현황

- 데이터 **677 트랙 / 화면 660곡(dedup) / 13밴드**. 워드클라우드 **라이브 노출 중**(렌더 동작 OK, 품질 보완 2-c만 남음).
- 백필 오리지널(1-a)·커버(1-b)·지역락 처리 **완료**(done 세션 14~19). 화면 곡수 526→**660**(+134). 끝까지 KR 지역락인 4곡만 제외.
- 다음 본류: **#1 워드클라우드 품질 보완 → #2 키워드 2D 클러스터.**

> ⏪ **롤백 지점 — `backup/main-20260630`** (local·origin): 백필 1-b 커버를 main에 올린 머지 `162f096`의 **직전 main = `d586ffb`**. 문제 시 `git revert -m 1 162f096 && git push origin main`(라이브 안전·권장) 또는 `git reset --hard d586ffb`(+force-push). (이전 백업 `backup/main-20260629`=`e062bca`는 워드클라우드 머지 `d6f05c7` 직전.)

---

## 우선순위

| 순 | 작업 | 난이도 | 상태 |
|----|------|--------|------|
| 1 | 워드클라우드 품질 보완 (2-c) | 중 | 🔄 렌더는 라이브, 품질 4건 남음 |
| 2 | 키워드 의미공간 2D 클러스터 | 중~높 | ⬜ 미착수 (1의 키워드 재활용) |
| — | (보류) 백필 1-c namedup 403 | — | url 품질 개선 · 후순위 |
| — | (보류) 진행도 Save/Load | 중~높 | 리스크 높음(덮어쓰기) |
| — | (백로그) youtube_rss Phase 2 / Phase 1.5 | — | precision 축적 후 |

원칙: **밴드 시각화 마무리(1) → 후속 확장(2)**. 보류·백로그는 별도 결정 사안.

---

## 1. 워드클라우드 품질 보완 (2-c) — 최우선

파이프라인·렌더 1차·TF-IDF 변별력 가중·가타카나 음차화·감성 데이터·라이브 머지는 **완료**(→ done 세션 17). 재생성 = `python tools/wordcloud/build_keywords.py`(멱등) → `python build.py`.

사용자 실사용 피드백 기반 남은 4건:

- **(A) yaml `ko` 검수**: `wordcloud/<band>.yaml`의 정렬/MT 초안 오역·노이즈 수정. **`# 기계번역 초안` 주석이 1순위 점검 대상.** (C와 직결)
- **(B) 가독성**: 키워드 과밀 → 표시 개수 60→~30-40, `gridSize`·여백·폰트 하한 ↑. (D와 연동 — 영역 넓히면 자연 해소)
- **(C) 무의미 키워드 + 변별력 가중**(`한·충성·텐` 등 일반·노이즈어): TF-IDF는 1차 적용됨 → 잔여는 **불용어 확장 + yaml 큐레이션(weight 0/삭제) + OVERRIDE 사전**으로. 잔여 노이즈 3종 = ⓐ영어외래어 음차(챤스→찬스) ⓑ의미불명 단편(시후·켄, align 오정렬·df=1) ⓒ문맥/극성 손실. **워드클라우드 핵심 개선 방향.**
- **(D) 배치 재결정** ⚠️ **사용자 결정 필요**: 우패널 탭이 좁아 워드클라우드에 부적합. 후보 = 유튜브 프레임 가로 2분할(아래=클라우드) / 전용 모달 / 하단 넓은 영역. 가독성(B)과 직결.

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

**밴드 퍼스널 컬러**(워드클라우드·클러스터 색, 확정):

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
