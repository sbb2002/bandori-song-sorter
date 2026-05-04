import yaml
import os
from jinja2 import Environment, FileSystemLoader

def build():
    yaml_dir = "data"
    template_dir = "templates"
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
                    if 'img_url' in album:
                        album['img_url'] = album['img_url'].replace('\\', '/')
                    albums_by_band[band_name].append(album)

    env = Environment(loader=FileSystemLoader(template_dir))
    try:
        template = env.get_template('index_template.html')
    except Exception as e:
        print(f"Error: 템플릿 로드 실패: {e}")
        return

    # 경로 정의
    static_paths = {
        "css": "./static/css/style.css",
        "js": "./static/js/script.js"
    }

    # 데이터 전달 (이 부분이 수정 포인트!)
    rendered_html = template.render(
        albums_by_band=albums_by_band,
        static_paths=static_paths
    )

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    print(f"✅ 빌드 완료! index.html이 생성되었습니다.")

if __name__ == "__main__":
    build()