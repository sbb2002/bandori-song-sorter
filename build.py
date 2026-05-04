import yaml
import os
from jinja2 import Environment, FileSystemLoader

def build():
    yaml_dir = "data"
    template_dir = "templates"
    # index.html을 루트 디렉토리에 생성하여 assets 폴더와 동일한 계층에 위치시킴
    output_dir = "." 

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
                
                album_list = content if isinstance(content, list) else [content]
                
                for album in album_list:
                    band_name = album.get('band', 'Others')
                    if band_name not in albums_by_band:
                        albums_by_band[band_name] = []
                    
                    # YAML 내 img_url 경로의 역슬래시를 슬래시로 통일하여 경로 처리 오류 방지
                    if 'img_url' in album:
                        album['img_url'] = album['img_url'].replace('\\', '/')
                        
                    albums_by_band[band_name].append(album)

    if not albums_by_band:
        print("Error: YAML 파일에서 앨범 데이터를 찾을 수 없습니다.")
        return

    env = Environment(loader=FileSystemLoader(template_dir))
    try:
        template = env.get_template('index_template.html')
    except Exception as e:
        print(f"Error: 템플릿 로드 실패: {e}")
        return

    rendered_html = template.render(albums_by_band=albums_by_band)

    # 루트 경로에 index.html 저장
    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f"✅ Build Success: index.html이 루트 디렉토리에 생성되었습니다. ({len(albums_by_band)}개 밴드 반영)")

if __name__ == "__main__":
    build()