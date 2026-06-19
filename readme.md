# 🎸 Bandori Song Sorter

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![YAML](https://img.shields.io/badge/Data-YAML-CB171E?style=flat-square&logo=yaml&logoColor=white)
![JS](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Bandori Song Sorter**는 뱅드림!(BanG Dream!)의 각 밴드별 수록곡 데이터를 바탕으로 나만의 **곡 단위** 선호도 랭킹을 만들고 관리할 수 있는 웹 프로젝트입니다. 밴드 선택 → 곡 리스트 → 랭크 팝업의 흐름으로, 곡을 짧게 누르면 유튜브로 재생하고 길게 누르면 **최애 / 차애 / 호 / 중간 / 불호** 5단계로 평가합니다. 파이썬 스크립트가 YAML 데이터를 정적 HTML로 빌드하며, PC와 모바일을 모두 지원하고, 랭크는 브라우저(localStorage)에 자동 저장됩니다.


## 💻 시작하기

### 1. 의존성 설치
프로젝트 실행을 위해 YAML 파서를 설치해야 합니다.
"""(코드)"""

### 2. 프로젝트 빌드
데이터를 수정하거나 새로운 밴드 파일을 추가한 후, 아래 빌드 스크립트를 실행하여 index.html을 생성하거나 갱신합니다.
"""(코드)"""

### 3. 결과 확인
로컬 디렉토리에 생성된 index.html 파일을 크롬(Chrome)이나 엣지(Edge) 등 웹 브라우저로 열어 정렬 기능을 확인하세요.


## 🚀 주요 기능

### 1. Data-Driven Build System
- 복잡한 HTML 수정 없이 `data/*.yaml` 파일만 편집하여 곡 정보를 업데이트할 수 있습니다.
- `build.py`가 YAML(앨범 단위)을 **곡 단위로 평탄화**하여 `window.SONG_DATA`로 주입한 `index.html`을 생성합니다. (밴드 내 중복 곡은 클라이언트에서 제거)

### 2. Multi-Device Sorting Interface
- **PC & Mobile 통일**: Pointer 이벤트 기반으로 마우스/터치 모두 동일하게 동작합니다. 곡을 **짧게 누르면 유튜브 재생**, **길게 누르면(또는 우클릭) 랭크 팝업**이 뜹니다.
- **5단계 감성 분류**: 최애 / 차애 / 호 / 중간 / 불호. 같은 티어를 다시 누르면 해제됩니다.
- **자동 저장**: 랭크는 localStorage에 저장되어 새로고침/재방문 후에도 유지됩니다.

### 3. Statistics & Visualization
- **밴드별 히스토그램**: 선택한 밴드(또는 전체)의 5단계 분포를 실시간 바 차트로 표시합니다.
- **전체 히트맵**: 모든 밴드 × 5티어 매트릭스로 밴드 간 선호도를 비교합니다.
- **진행률**: 평가한 곡 수를 헤더에 표시합니다.

### 4. Sharing
- **링크 복사**: 현재 밴드/필터에 해당하는 곡의 유튜브 링크를 DC인사이드 자동 렌더 형식(링크 + 빈 줄)으로 복사합니다.
- **Download**: 전 밴드 히스토그램 + 히트맵을 한 장의 PNG 이미지로 저장합니다.

### 테스트
```
npm test   # node --test — core.js 순수 함수(중복 제거/집계/링크 생성) 단위 테스트
```


## 🛠 기술 스택

- **Backend (Build)**: Python 3.10+, PyYAML
- **Frontend**: 
  - **Structure**: HTML5 (Semantic Tags)
  - **Style**: CSS3 (Responsive Design, Flexbox/Grid)
  - **Script**: Vanilla JavaScript (Touch/Mouse Event Handling)
- **Data Format**: YAML

