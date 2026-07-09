# Umami

## 역할
라이브 사이트 방문자 수 카운팅(analytics). 자체 호스팅 없이 **cloud.umami.is** 호스팅형 서비스를
쓴다.

## 동작 방식
`src/templates/index_template.html`의 `</head>` 직전에 스크립트 태그 하나가 박혀 있다:
```html
<script defer src="https://cloud.umami.is/script.js" data-website-id="7185d432-2c87-41e5-8166-46125dc76e33"></script>
```
빌드(`python src/build.py`) 시 이 태그가 그대로 `index.html`에 포함돼 배포된다.

## 필요한 키
**없음.** `data-website-id`는 umami가 어느 사이트의 통계인지 구분하는 **공개 식별자**이지
비밀값이 아니다(클라이언트 HTML에 그대로 노출돼도 문제없음). 대시보드 로그인은 별도로 사용자의
umami 계정(이메일/비번 또는 OAuth)로 하며, 그 계정 정보는 이 저장소·문서 범위 밖이다.

## 만료주기
`website-id`는 umami 계정에서 그 사이트를 삭제하지 않는 한 고정. 다만 **umami cloud 무료 플랜은
이벤트/방문 한도가 있을 수 있음** — 대시보드에서 플랜·한도 확인 필요(계정 종속 정보라 여기 기록 안 함).

## 장애 시 확인
1. 라이브 사이트에서 브라우저 개발자도구 → Network 탭에 `script.js` 요청이 200으로 잡히는지.
2. 통계가 안 잡히면: (a) 배포된 `index.html`에 스크립트 태그가 실제로 있는지(뷰소스로 확인) —
   없다면 `src/templates/index_template.html` 수정이 아직 `main`에 안 올라갔거나 배포가 안 된 것
   ([github-pages.md](github-pages.md) 참조), (b) `data-website-id`가 대시보드의 사이트 ID와
   일치하는지, (c) 광고 차단기가 `cloud.umami.is` 요청을 막고 있는지(사용자 측 문제, 정상).
3. 세션 31~32 사례: 스크립트를 로컬 `index.html`에만 넣고 커밋해서 다음 CI 재빌드 때 사라질
   뻔했음(`index.html`은 gitignore 대상 — 반드시 템플릿 파일을 고쳐야 함).
