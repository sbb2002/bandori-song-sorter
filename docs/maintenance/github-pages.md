# GitHub Pages

## 역할
이 앱의 **라이브 서비스 자체**를 호스팅한다 — https://sbb2002.github.io/bandori-song-sorter/

## 동작 방식
- `index.html`은 저장소에 **커밋하지 않는다**(`.gitignore`의 `/index.html`, "Option A" 결정).
  대신 `.github/workflows/deploy.yml`이 `main` push 시(`src/**`·`static/**`·`assets/**` 경로
  변경분) `python src/build.py`로 매번 새로 빌드해 GitHub Pages 아티팩트로 배포한다.
- 스테이징 트리(`_site/`)에는 `index.html` + `static/` + `assets/` + `src/content/cluster/onsets/`만
  포함(곡·워드클라우드·클러스터 데이터는 `index.html`에 인라인되므로 별도 포함 불필요).
- ⚠️ **로컬 `index.html`을 직접 수정해도 라이브에 반영되지 않는다** — 다음 `main` push 때 CI가
  덮어쓴다. 실제 소스는 `src/templates/index_template.html`이다(umami 스크립트를 로컬
  `index.html`에만 넣었다가 유실될 뻔한 사례, `docs/working/done.md` 참조).

## 필요한 키
**없음.** 순수 저장소 설정값으로만 동작한다.

## 필수 설정(저장소별 1회)
저장소 **Settings → Pages → Source = "GitHub Actions"** 로 전환돼 있어야 한다(`deploy.yml` 상단
주석에 명시). 저장소를 새로 만들거나 포크했다면 이 설정부터 확인.

## 만료주기
없음. 단, `deploy.yml`의 `permissions: pages: write, id-token: write`가 유지돼야 하고, 저장소가
private로 전환되면 Pages 요금제 정책이 달라질 수 있음(현재 public).

## 장애 시 확인
1. Actions 탭 → "Build & deploy (Pages)" 워크플로 실행 로그.
2. `python src/build.py` 단계 실패 → 템플릿(Jinja2) 문법 오류나 `src/content/*` 데이터 파일 문제.
3. 배포는 됐는데 내용이 안 바뀜 → 방금 수정한 게 `index.html`이 아니라 `src/templates/index_template.html`인지
   확인(위 "동작 방식" 참고).
4. Pages 자체가 404 → Settings → Pages에서 Source 설정이 풀려있지 않은지 확인.
