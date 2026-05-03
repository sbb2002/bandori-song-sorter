import yaml
import os
from jinja2 import Environment, FileSystemLoader

def build():
    # 0. 경로 설정
    yaml_dir = "data"
    template_dir = "templates"
    output_dir = "docs"

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
                    if isinstance(band_albums, list):
                        albums.extend(band_albums)
                    else:
                        albums.append(band_albums)

    if not albums:
        print("Error: YAML 파일에서 앨범 데이터를 찾을 수 없습니다.")
        return

    # 2. Jinja2 환경 설정 (tojson 필터 지원)
    env = Environment(loader=FileSystemLoader(template_dir))
    try:
        template = env.get_template('index_template.html')
    except Exception as e:
        print(f"Error: 템플릿을 로드할 수 없습니다: {e}")
        return

    # 3. 데이터 렌더링
    rendered_html = template.render(albums=albums)

    # 4. 결과 저장
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f"✅ Build Success: {len(albums)}개의 앨범 데이터가 {output_path}에 생성되었습니다.")

if __name__ == "__main__":
    build()