import json
from jinja2 import Template

# 1. 앨범 데이터 (실제로는 data.py에서 가져오거나 크롤링할 수 있음)
albums = [
    {"id": "1", "title": "Fire Bird", "band": "Roselia", "img": "path/to/img1.jpg", "yt": "https://youtu.be/xxx"},
    {"id": "2", "title": "A DECLARATION OF ×××", "band": "RAISE A SUILEN", "img": "path/to/img2.jpg", "yt": "https://youtu.be/yyy"},
    {"id": "3", "title": "Ave Mujica", "band": "Ave Mujica", "img": "path/to/img3.jpg", "yt": "https://youtu.be/zzz"},
]

# 2. HTML 템플릿 읽기
with open('templates/index_template.html', 'r', encoding='utf-8') as f:
    template_str = f.read()

# 3. 템플릿 엔진 실행
template = Template(template_str)
rendered_html = template.render(albums=albums)

# 4. 결과 저장 (GitHub Pages는 보통 docs/ 폴더를 인식 가능)
with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(rendered_html)

print("Build Complete: docs/index.html 생성됨")