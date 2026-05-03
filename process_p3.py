import os
import re

ALBUMS_DIR = "raw/albums"


def extract_numbering_and_title(first_line: str) -> tuple[str, str]:
    """
    첫 줄에서 numbering과 album_title을 추출합니다.
    예: "==== 1st Album: ONE OF US ====" -> ("1st", "ONE OF US")
    """
    cleaned = first_line.strip("= ").strip()
    
    if ":" in cleaned:
        parts = cleaned.split(":", 1)
        left = parts[0].strip()  # "1st Album" 또는 "Mini Album 1"
        right = parts[1].strip()  # 앨범 제목
        
        # left에서 numbering 추출 (1st, 2nd, 3rd, Mini, 등)
        numbering_match = re.search(r'\b(1st|2nd|3rd|4th|5th|Mini|EP)\b', left, re.IGNORECASE)
        if numbering_match:
            numbering = numbering_match.group(1)
        else:
            numbering = left
        
        return numbering, right
    
    return "-", cleaned


def parse_track_line(line: str) -> tuple[str, str] | None:
    """
    트랙 라인에서 track_number와 name을 추출합니다.
    예: "|| 01 || ON YOUR MARK ||" -> ("01", "ON YOUR MARK")
    """
    parts = line.split("||")
    if len(parts) < 3:
        return None
    
    track_number = parts[1].strip()
    track_name = parts[2].strip()
    
    if track_number and track_name:
        return track_number, track_name
    
    return None


def format_yaml_with_spacing(albums_data):
    """album_title이 변할 때마다 한 줄씩 띄운 YAML 형식 반환"""
    lines = []
    
    for idx, album in enumerate(albums_data):
        if idx > 0:
            lines.append("")  # album_title이 바뀔 때마다 한 줄 띄우기
        
        lines.append(f"- band: {repr(album['band'])}")
        lines.append(f"  numbering: {repr(album['numbering'])}")
        lines.append(f"  album_title: {repr(album['album_title'])}")
        lines.append(f"  img_url: {repr(album['img_url'])}")
        lines.append(f"  tracks:")
        
        for track in album['tracks']:
            lines.append(f"    - track_number: {repr(track['track_number'])}")
            lines.append(f"      name: {repr(track['name'])}")
            lines.append(f"      url: {repr(track['url'])}")
    
    return "\n".join(lines)


def process_p_files():
    """raw/albums 아래의 모든 p_*.txt 파일을 YAML로 변환하고 band별로 분리 저장"""
    band_albums = {}
    
    for root, dirs, files in os.walk(ALBUMS_DIR):
        for filename in sorted(files):
            if not filename.startswith("p_") or not filename.endswith(".txt"):
                continue
            
            band_name = os.path.basename(root)
            filepath = os.path.join(root, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            
            if not lines:
                continue
            
            numbering, album_title = extract_numbering_and_title(lines[0])
            
            tracks = []
            for line in lines[1:]:
                track_info = parse_track_line(line)
                if track_info:
                    track_number, track_name = track_info
                    tracks.append({
                        "track_number": track_number,
                        "name": track_name,
                        "url": "-"
                    })
            
            album_data = {
                "band": band_name,
                "numbering": numbering,
                "album_title": album_title,
                "img_url": "-",
                "tracks": tracks
            }
            
            if band_name not in band_albums:
                band_albums[band_name] = []
            band_albums[band_name].append(album_data)
    
    # band별로 YAML 파일 생성
    os.makedirs("data", exist_ok=True)
    total_albums = 0
    
    for band_name in sorted(band_albums.keys()):
        albums = band_albums[band_name]
        output_filename = f"{band_name}.yaml"
        output_path = os.path.join("data", output_filename)
        
        yaml_content = format_yaml_with_spacing(albums)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content + "\n")
        
        total_albums += len(albums)
        print(f"생성: {output_path} ({len(albums)}개 앨범)")
    
    print(f"\n처리 완료: 총 {total_albums}개 앨범, {len(band_albums)}개 band별 파일 생성")


if __name__ == "__main__":
    process_p_files()
