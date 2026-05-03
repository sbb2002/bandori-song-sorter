import yaml
import os
from jinja2 import Template

def build():
    # 0. yaml dir에 접근
    yaml_dir = "data"

    # 1. data/ 폴더의 모든 YAML 파일 로드
    albums = []
    if not os.path.exists(yaml_dir):
        print(f"Error: {yaml_dir} 폴더를 찾을 수 없습니다.")
        return

    for filename in os.listdir(yaml_dir):
        if filename.endswith('.yaml'):
            yaml_path = os.path.join(yaml_dir, filename)
            with open(yaml_path, 'r', encoding='utf-8') as f:
                band_albums = yaml.safe_load(f)
                if band_albums:
                    albums.extend(band_albums)

    if not albums:
        print("Error: YAML 파일에서 앨범 데이터를 찾을 수 없습니다.")
        return

    # 2. HTML 템플릿 읽기 (기존에 작성된 templates/index_template.html 활용)
    template_path = 'templates/index_template.html'
    if not os.path.exists(template_path):
        print(f"Error: {template_path} 파일을 찾을 수 없습니다.")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        template_str = f.read()

    # 3. Jinja2 템플릿 엔진 렌더링
    template = Template(template_str)
    # YAML의 각 항목이 template에서 사용하는 변수명(albums)과 일치하도록 전달
    rendered_html = template.render(albums=albums)

    # 4. 결과 저장 (GitHub Pages 배포용 docs 폴더)
    output_dir = 'docs'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f"Build Success: {len(albums)}개의 앨범 데이터가 {output_path}에 반영되었습니다.")

if __name__ == "__main__":
    build()