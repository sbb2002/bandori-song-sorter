import yaml
import os
import json
from jinja2 import Environment, FileSystemLoader


def load_senti(path="tools/wordcloud/senti_lexicon.yaml"):
    """감성 사전(표시텍스트→극성 -2..+2). 없으면 빈 dict(감성 뷰 중립)."""
    if not os.path.exists(path):
        return {}
    doc = yaml.safe_load(open(path, encoding='utf-8'))
    return (doc or {}).get('words', {}) or {}


def load_wordclouds(wc_dir="wordcloud"):
    """wordcloud/<band>.yaml → {band: {song_count, keywords:[{jp,ko,weight,senti}]}}.

    build_keywords.py 산출물(커밋·사용자 편집). 없으면 빈 dict(워드클라우드 탭 비활성).
    senti = senti_lexicon.yaml 룩업(표시텍스트 ko‖jp 기준, 미등재=0=중립).
    """
    out = {}
    if not os.path.isdir(wc_dir):
        return out
    senti = load_senti()
    for filename in sorted(os.listdir(wc_dir)):
        if not filename.endswith('.yaml'):
            continue
        with open(os.path.join(wc_dir, filename), 'r', encoding='utf-8') as f:
            doc = yaml.safe_load(f)
        if not doc or not doc.get('keywords'):
            continue
        band = doc.get('band') or filename[:-5]
        kws = []
        for k in doc['keywords']:
            if not k.get('jp'):
                continue
            ko = (k.get('ko') or '').strip()
            text = ko or k.get('jp', '')
            kws.append({'jp': k.get('jp', ''), 'ko': ko,
                        'weight': k.get('weight', 1), 'senti': senti.get(text, 0)})
        out[band] = {'song_count': doc.get('song_count', 0), 'keywords': kws}
    return out


def build():
    """data/*.yaml(앨범 단위)를 곡 단위로 평탄화하여 index.html을 생성한다.

    - 앨범의 tracks를 곡 리스트로 펼친다. 중복 제거는 클라이언트(core.js)가 담당.
    - 밴드 순서는 파일명 정렬 기준 첫 등장 순서를 따른다.
    - window.SONG_DATA = { bands: [...], songsByBand: {band: [{title,url,album,img}]} }
    """
    yaml_dir = "data"
    template_dir = "templates"
    output_dir = "."

    if not os.path.exists(yaml_dir):
        print(f"Error: {yaml_dir} 폴더를 찾을 수 없습니다.")
        return

    bands = []                 # 첫 등장 순서 보존
    songs_by_band = {}

    for filename in sorted(os.listdir(yaml_dir)):
        if not filename.endswith('.yaml'):
            continue

        yaml_path = os.path.join(yaml_dir, filename)
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        if not content:
            continue

        album_list = content if isinstance(content, list) else [content]

        for album in album_list:
            band = album.get('band', 'Others')
            album_title = album.get('album_title', '')
            img_url = (album.get('img_url') or '').replace('\\', '/')

            if band not in songs_by_band:
                songs_by_band[band] = []
                bands.append(band)

            for track in (album.get('tracks') or []):
                songs_by_band[band].append({
                    'band':  band,
                    'title': track.get('name', ''),
                    'url':   track.get('url') or '',
                    'album': album_title,
                    'img':   img_url,
                })

    if not bands:
        print("Error: YAML 파일에서 곡 데이터를 찾을 수 없습니다.")
        return

    song_data = {'bands': bands, 'songsByBand': songs_by_band}
    wordcloud_data = load_wordclouds()

    env = Environment(loader=FileSystemLoader(template_dir))
    try:
        template = env.get_template('index_template.html')
    except Exception as e:
        print(f"Error: 템플릿 로드 실패: {e}")
        return

    static_paths = {
        "css":  "./static/css/style.css",
        "core": "./static/js/core.js",
        "js":   "./static/js/script.js",
    }

    # <script> 안에 안전하게 주입: '<'만 이스케이프해도 </script> 브레이크아웃 방지.
    # (구조적 JSON에는 '<'가 없고 문자열 값 내부에서만 등장 → 유효 JSON 유지)
    song_data_json = json.dumps(song_data, ensure_ascii=False).replace('<', '\\u003c')
    wordcloud_data_json = json.dumps(
        wordcloud_data, ensure_ascii=False).replace('<', '\\u003c')

    rendered_html = template.render(
        song_data_json=song_data_json,
        wordcloud_data_json=wordcloud_data_json,
        static_paths=static_paths,
    )

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    total = sum(len(v) for v in songs_by_band.values())
    wc = len(wordcloud_data)
    print(f"[OK] Build Success: index.html 생성 완료 "
          f"(밴드 {len(bands)}개, 곡 {total}개, 워드클라우드 {wc}밴드)")


if __name__ == "__main__":
    build()
