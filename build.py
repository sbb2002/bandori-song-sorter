import yaml
import os
from jinja2 import Environment, FileSystemLoader

def build():
    yaml_dir = "data"
    template_dir = "templates"
    output_dir = "docs"

    # 1. 데이터를 밴드별로 그룹화할 딕셔너리 준비
    albums_by_band = {}
    
    if not os.path.exists(yaml_dir):
        print(f"Error: {yaml_dir} 폴더를 찾을 수 없습니다.")
        return

    for filename in os.listdir(yaml_dir):
        if filename.endswith('.yaml'):
            yaml_path = os.path.join(yaml_dir, filename)
            with open(yaml_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if not content: continue
                
                # 리스트 형태든 단일 객체든 처리
                album_list = content if isinstance(content, list) else [content]
                
                for album in album_list:
                    # 'band' 키가 없으면 'Others'로 분류
                    band_name = album.get('band', 'Others')
                    if band_name not in albums_by_band:
                        albums_by_band[band_name] = []
                    albums_by_band[band_name].append(album)

    if not albums_by_band:
        print("Error: YAML 파일에서 앨범 데이터를 찾을 수 없습니다.")
        return

    # 2. Jinja2 환경 설정
    env = Environment(loader=FileSystemLoader(template_dir))
    try:
        template = env.get_template('index_template.html')
    except Exception as e:
        print(f"Error: 템플릿 로드 실패: {e}")
        return

    # 3. 렌더링 (이제 albums 대신 albums_by_band 전달)
    rendered_html = template.render(albums_by_band=albums_by_band)

    # 4. 결과 저장
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f"✅ Build Success: {len(albums_by_band)}개 밴드의 데이터가 반영되었습니다.")

if __name__ == "__main__":
    build()