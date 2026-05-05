# 🎸 Bandori Album Sorter

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![YAML](https://img.shields.io/badge/Data-YAML-CB171E?style=flat-square&logo=yaml&logoColor=white)
![JS](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Bandori Album Sorter**는 뱅드림!(BanG Dream!)의 각 밴드별 앨범과 수록곡 데이터를 바탕으로 나만의 앨범 티어리스트를 만들고 관리할 수 있는 웹 프로젝트입니다. 파이썬 스크립트를 통해 YAML 데이터를 정적인 HTML 페이지로 빌드하며, PC와 모바일 환경을 모두 지원합니다.


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
- 복잡한 HTML 수정 없이 `data/*.yaml` 파일만 편집하여 앨범 정보를 업데이트할 수 있습니다.
- `build.py` 스크립트가 YAML 데이터를 파싱하여 앨범 커버, 트랙 리스트, 유튜브 링크가 포함된 `index.html`을 자동 생성합니다.

### 2. Multi-Device Sorting Interface
- **PC & Mobile Support**: 마우스 드래그는 물론 모바일의 터치 이벤트(`touchstart`, `touchmove`, `touchend`)를 모두 지원하여 어디서나 자유롭게 순서를 변경할 수 있습니다.
- **Intuitive UI**: 앨범 아트워크를 드래그하여 직관적으로 티어를 분류하고 정렬합니다.

### 3. Statistics & Visualization (Planned)
- 밴드별/티어별 곡 분포도를 차트(Heatmap, Stacked Bar Chart)로 시각화하여 내 취향의 통계를 한눈에 확인할 수 있습니다.


## 🛠 기술 스택

- **Backend (Build)**: Python 3.10+, PyYAML
- **Frontend**: 
  - **Structure**: HTML5 (Semantic Tags)
  - **Style**: CSS3 (Responsive Design, Flexbox/Grid)
  - **Script**: Vanilla JavaScript (Touch/Mouse Event Handling)
- **Data Format**: YAML

