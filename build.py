import yaml
import os
import json # 추가: 안전한 데이터 변환을 위해
from jinja2 import Environment, FileSystemLoader

def build():
    # 0. 설정 및 경로
    yaml_dir = "data"
    template_dir = "templates"
    output_dir = "docs"

    # 1. data/ 폴더의 모든 YAML 파일 로드 (기존 로직 유지)
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
        print("Error: 앨범 데이터를 찾을 수 없습니다.")
        return

    # 2. Jinja2 환경 설정 (tojson 필터를 위해 Environment 사용 추천)
    # 단순히 Template()을 쓰는 것보다 이 방식이 더 체계적이고 확장성이 좋습니다.
    env = Environment(loader=FileSystemLoader(template_dir))
    
    try:
        template = env.get_template('index_template.html')
    except Exception as e:
        print(f"Error: 템플릿 파일을 읽는 중 오류 발생: {e}")
        return

    # 3. 렌더링
    rendered_html = template.render(albums=albums)

    # 4. 결과 저장
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f"✅ Build Success: {len(albums)}개의 앨범이 반영되었습니다.")

if __name__ == "__main__":
    build()