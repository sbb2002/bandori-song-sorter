# HANDOFF: bandori-song-sorter — 남은 작업

해야 할 것·남은 것만 담습니다. **완료된 작업 기록은 [done.md](done.md)** 참조.
(참고 사실 — v2 표시 범위, 라이브/원격 URL, 환경 등 — 도 done.md 상단에 정리.)

마지막 갱신: #1 데이터 정합성 검수 **핵심 완료** — C2 배치 40 + 중복MV 2 삭제 + C1 redundant 24 삭제 + 빈url 16 처리(보강 2/제거 14). **undefined 더미 블록 0 · 빈url 0 · 전곡(517) 재생가능**. 곡수 561→517. 남은 건 곡명 정규화(rule 2, 후순위)뿐. (branch `feature/song-validator`, main 미머지) 상세 아래 #1. (2026-06-25)

> **ux-02.md 1·2·3·6·7번 + youtube_rss 자동화 완료**. 상세는 [done.md](done.md). 옵션 A(랭크순)는 `feature/ux-02-opt-a` 백업, 진행률 링 conic 시안은 `feature/ux-02-ring-conic` 백업.
> 아래는 남은 3건을 **구현 난이도 낮고 기존 기능을 덜 해치는 순**으로 유지.

---

## 작업 순서 (쉽고 안전 → 어렵고 위험)

| 순 | 작업 | 난이도 | 기존기능 리스크 |
|----|------|--------|-----------------|
| 1 | 데이터 품질 검수 | 중(수작업) | 중(곡 데이터 변경→회귀) |
| 2 | 진행도 Save/Load | 중~높 | 높음(진행 덮어쓰기→손실) |
| 3 | 한국 지역락 대응 | 높(불확실) | 중(감지·대체 미정) |

원칙: **곡 데이터 변경(1) → 저장 덮어쓰기(2) → 방안 불확실(3).**

---

> ⚠️ **진행률 링(done 세션 11)에서 보류된 열린 결정**: 70% Green은 **링 색상일 뿐**이고, "70% 이상만 최애밴드 표시 자격" **하드게이트는 미도입**. 현 최애밴드는 스코어링 수축(`w(n)`)으로만 선정. 게이트 도입 여부는 별도 결정 사안으로 남김(ux-02.md #2 "최애밴드 표시 자격 조건"과 연결).

> ℹ️ **youtube_rss 자동화 운영 메모(완료된 기능의 낮은 우선순위 후속)**: ① CI에선 길이 스크랩이 막혀(`length_s=null`, 데이터센터 IP consent wall) **길이필터 비활성·`variant_tag`만 작동** → 아래 #1 데이터 품질의 oEmbed/길이 로직과 공유해 보강 가능. ② `tools/rss_seen.json`(폐기 프로토타입 산출물) untracked 잔존 → 삭제 가능. ③ Phase 2(고신뢰 auto-merge)·Phase 1.5(build+deploy 자동)는 precision 축적 후 검토. 상세는 done.md 세션 13.

### 1. 데이터 정합성 검수 — **핵심 완료** (branch `feature/song-validator`, main 미머지) · 곡수 561→517
**도구**(전부 텍스트 기반 = YAML 포맷·따옴표 보존, dry-run 기본 + `--apply`, 적용 후 재파싱·손실0 검증 내장):
- `tools/verify_links.py` — 읽기전용 triage(data 무변경). L0 오프라인(A빈url·B url오류·C undefined분류·D앨범중복·E동명다른영상) / L1 `--oembed` / L2 `--length`. 캐시 `verify_cache.json`(untracked).
- `tools/execute_placement.py` — C2 배치 실행기(`c2_placement.csv` 입력).
- `tools/delete_redundant.py` — C1 redundant 삭제(undef 블록 *범위 내에서만* 제거 → 정규앨범 보존, 빈 undef 블록 드롭).
- `tools/resolve_empty.py` — 빈url 정리(ENRICH 매핑은 New Singles 보강, 나머지 제거, 빈 undef 드롭).
youtube_rss의 video_id/norm_name/길이/oEmbed/insert_track 재사용(중복정의 없음). **로컬 전용**(L2 길이 스크랩은 CI consent wall로 막힘).
- Layer0(오프라인): A 빈url · B url오류(같은 video_id를 다른 곡명이 가리킴) · C undefined분류(redundant/unique/empty) · D 앨범중복(정상) · E 동명-다른영상.
- L1 `--oembed`: 죽은링크(404/비공개)+제목대조. L2 `--length`: 풀버전/TV Size. `--all`/`--json`. 캐시 `tools/verify_cache.json`(untracked).

**확립된 규칙**(데이터 정리 기준):
1. **소스 우선순위 음원(Topic) > MV > 라이브.** 라이브는 사용자가 직접 추가. 같은 곡 중복 시 더 우선되는 소스만 남김.
2. **곡명 = 공식 유튜브 채널 표기.** 영문음차(romaji) 지양. 미반영분 다수 존재(전체 정규화는 별도 패스 가능).
3. **동명이곡은 모두 유지**(원곡 vs 타곡 커버, JP vs English Ver. 등). 앱은 `band::title`로 식별·`normalizeTitle`이 `(Cover)`/`(English)` 안 지우므로 title만 다르면 별개. ⚠️ title 완전 동일하면 충돌→반드시 구분 저장.
4. **album_title은 화면 미표시**(`isCover=album==='Covers' || /\(cover\)/i.test(title)`에만 사용, script.js:149). 정밀 album_title은 현재 기능영향 0, 미래 "수록 앨범 메타데이터" 기능용.
5. 신곡 검수 워크플로우: 자동 PR 우선, 결함 시에만 CSV(`--digest` 미구현)+알림. (memory `rss_review_workflow`)

**완료**(커밋 b765cc0→1379d88): malformed 곡명 3 · wrong-url 7(B, 어쿠스틱5 포함, oEmbed로 정답 확정) · 커버 4 → Covers 이동(공식명+업로드일) · 음원우선 정리(mygo 静降想 MV삭제 / morfonica 2 음원교체 / ave_mujica 顔 MV교체).

**완료(이번 세션, 미커밋)** — undefined 더미앨범 전량 해소:
1. **C2 유일본 40 배치 + 중복 MV 2 삭제**(`execute_placement.py`). undefined 더미 36 → 각 밴드 `New Singles`(numbering `Single`, 없는 밴드 afterglow·mygo·ikka·millsage 블록 신설, img `_fallback.png`). various_artists 4는 서브유닛 앨범(Glitter*Green/Chispa/Sumimi) `numbering:undefined`만 결함 → de-undef. 사용자 romaji→공식명 7 반영(예 `Haruhikage (Original)`→`春日影`, 정규 `春日影 (MyGO!!!!! ver.)`와 별개). 삭제(음원우선·손실0): mugendai `Mutant Mutant`(MV) · poppin `DOKI DOKI DATE`(MV).
2. **C1 redundant 24 삭제**(`delete_redundant.py`). undefined가 정규앨범과 동일 video_id → 손실0 검증 후 일괄 제거. 빈 undef 블록(ave_mujica·pastel_palettes) 드롭. 곡수 555→531.
3. **빈url 16 처리**(`resolve_empty.py`, 정책 "보강 후 잔여 제거"). **보강 2**: RAS `WHAT AN EXPLOSION`/`RUNAWAY STAR`(15th single, 2026-06-10 발매 — 입력 당시 미발매라 빈url이었음. WebSearch+oEmbed `RAISE A SUILEN - Topic` 검증) → New Singles(tn 발매일). **제거 14**: mygo `致並跡 -`×3(빈슬롯) + afterglow `IGNITE GLOW`(음원중복) + 보강실패 10(GLAMOROUS SKY·紅蓮の弓矢·Take it easy 등 — 게임곡/커버라 공식 음원 없음). 잔존 빈 undef 블록(afterglow·hello·morfonica·mygo·poppin·raise·roselia + ikka·millsage·mugendai) 전량 드롭. 곡수 531→517.
- **결과: undefined 더미 블록 0 · 빈url 0 · 전곡 517 video_id 보유(재생가능) · B/C1/C2 모두 0.** `index.html` 재빌드 완료(517곡).
- ⚠️ **JS 카운트 테스트는 실재하지 않음**(core.test.js는 합성 fixture만 단언) → 곡수 변동 시 갱신 불필요.
- 잔존(untracked): `c2_placement.csv`(40행, 추적가능). `verify_cache.json`(oEmbed 캐시)은 재생성 가능이라 이미 `.gitignore` 등재됨.

**남은 #1(후순위)**:
- **곡명 정규화(rule 2)**: romaji/음차 표기 다수 잔존 → 공식 채널 표기로 별도 패스 가능(기능영향 0, album_title처럼 메타품질 개선용).
- `tools/rss_seen.json` 폐기 잔재 삭제 가능.

ℹ️ 곡수 변동 시 `python build.py`로 index.html 재생성(JS 카운트 테스트 없음, 위 확인).

### 2. 진행도 Save/Load (ux-02.md #4) — 난이도 중~높 · 리스크 높음 · 후순위
내 진행상황을 **json으로 백업/공유**. Load 시 즉시 로딩 아니라 **Mine/Others 선택**(Mine=내 것 즉시 로드, Others=타인 것 로드 대화창). 내 진행은 항상 백업. 공유는 디씨 등 커뮤니티 첨부 상정.
- ⚠️ **Load = 기존 진행 덮어쓰기 → 데이터 손실 위험**. 로드 전 현재 진행 자동 백업·복구 경로 선설계 필수.
- **후순위**: 디씨 json 첨부가 금기/헤비하면 이 기능 반려 가능. 구현성·안정성·커뮤니티 배포가능성 선검토 필요. (코멘트는 세션 12에서 별도 키 `bandori-song-comments-v1`로 구현됨 → Save/Load 직렬화 범위에 `ranks`와 함께 코멘트를 포함할지 확정 필요.)

### 3. 한국 지역락 노래 대응 (ux-02.md #5) — 난이도 높(불확실) · 리스크 중
일부 곡이 한국 지역락일 수 있음 → 대응책 필요.
- 미정 영역: 지역락 **감지 방법**(클라이언트에서 판별 난해), **대체 링크/표기** 정책. 방안 구상부터 필요. #1 데이터 품질 검수와 oEmbed 점검 로직 일부 공유 가능.
