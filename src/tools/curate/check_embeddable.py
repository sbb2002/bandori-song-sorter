"""
재생불가 곡 탐지 + 원인 분류(plb) — docs/working/urgent.md 대응.

증상: 앱 유튜브 iframe 에서 일부 곡이
  '동영상을 재생할 수 없음. 동영상을 볼 수 없습니다.'
로 뜸. 이 문구는 지역락/임베드차단/삭제/연령제한을 모두 덮는 '일반 메시지'라
원인을 따로 가려야 한다. 그래서 두 신호를 합친다:

  (1) ground truth — watch 페이지 playabilityStatus (한국 IP, hl=ko&gl=KR).
      사용자가 실제로 보는 재생 가능 여부 그 자체. status ∈
      {OK, UNPLAYABLE, LOGIN_REQUIRED, ERROR, ...} + reason.
      ⚠️ 반드시 로컬(한국 가정 IP)에서 실행. 데이터센터 IP 는 consent wall.
  (2) 원인 보강 — YouTube Data API status/contentDetails:
      embeddable(임베드 허용) · regionRestriction(지역) · privacyStatus.

plb 칼럼 분류:
  region_blocked    : KR 지역제한 (regionRestriction 이 KR 차단/미허용) — 영상 자체는 생존.
  embed_disabled    : status.embeddable=false (외부 사이트 재생만 차단).
  deleted_or_private: Data API 미응답 = 삭제/비공개/잘못된 id.
  login_required    : 연령제한 등 로그인 요구 → iframe 재생불가.
  unplayable        : 위로 안 잡히는 기타 재생불가(reason 참조).
  ok                : 정상(플래그 안 함).

산출물: tools/curate/fix_url.csv  [song_name, current_url, modified_url, plb]
  - modified_url 공란. 사람이 채우면 그 url 로 교체, 공란이면 곡 삭제(docs/working/urgent.md 규약).
캐시: tools/curate/plb_cache.json (watch 스크랩 결과). 재실행 시 네트워크 재요청 안 함.
"""
import os
import re
import sys
import csv
import json
import time
from pathlib import Path

# youtube_rss / youtube_api 는 tools/collect/ 에 있음(공유 모듈).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collect"))
from youtube_rss import DATA_DIR, video_id, http_get  # noqa: E402
from youtube_api import api_get, load_env_key, _batched  # noqa: E402

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[3]   # src/tools/curate/<file> → repo root
OUT_CSV = ROOT / "src" / "tools" / "curate" / "fix_url.csv"
CACHE = ROOT / "src" / "tools" / "curate" / "plb_cache.json"
WATCH = "https://www.youtube.com/watch?v={}&hl=ko&gl=KR"


def load_tracks():
    """모든 src/content/songs/*.yaml 에서 (band, album, name, url, vid) 트랙을 순서대로."""
    rows = []
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".yaml"):
            continue
        albums = yaml.safe_load((DATA_DIR / fn).read_text(encoding="utf-8")) or []
        for al in albums:
            for t in (al.get("tracks") or []):
                url = t.get("url")
                rows.append({
                    "band": al.get("band", ""),
                    "album": al.get("album_title", ""),
                    "name": t.get("name", ""),
                    "url": url,
                    "vid": video_id(url),
                })
    return rows


def fetch_api_status(vids, key):
    """{video_id: {embeddable, privacyStatus, region}}. 누락 = 삭제/비공개."""
    out = {}
    for batch in _batched(list(vids), 50):
        data = api_get("videos",
                       {"part": "status,contentDetails", "id": ",".join(batch)}, key)
        for it in data.get("items", []):
            st, cd = it.get("status", {}), it.get("contentDetails", {})
            out[it["id"]] = {
                "embeddable": st.get("embeddable"),
                "privacyStatus": st.get("privacyStatus"),
                "region": cd.get("regionRestriction"),
            }
    return out


def scrape_playability(vid):
    """watch 페이지(KR)에서 (status, reason). 실패 시 ('?' , '')."""
    try:
        html = http_get(WATCH.format(vid))
        m = re.search(r'"playabilityStatus":\{"status":"([^"]+)"'
                      r'(?:,"reason":"([^"]*)")?', html)
        if m:
            return m.group(1), (m.group(2) or "")
        return "?", ""
    except Exception as e:
        return "ERR", repr(e)[:80]


def fetch_playability(vids):
    """{video_id: [status, reason]} — 캐시 우선, 미캐시만 네트워크."""
    cache = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    todo = [v for v in vids if v not in cache]
    if todo:
        print(f"watch playabilityStatus 스크랩(KR): {len(todo)}개 "
              f"(캐시 {len(vids) - len(todo)}개 재사용)")
        for i, v in enumerate(todo, 1):
            cache[v] = list(scrape_playability(v))
            if i % 50 == 0 or i == len(todo):
                print(f"  ...{i}/{len(todo)}")
                CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            time.sleep(0.12)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return cache


def region_kr_blocked(rr):
    if not rr:
        return False
    blk, alw = rr.get("blocked"), rr.get("allowed")
    return bool((blk and "KR" in blk) or (alw and "KR" not in alw))


def classify(row, api_map, plb_map):
    """트랙 1건 → plb 라벨. None 이면 정상(재생 가능)."""
    vid = row["vid"]
    if not vid:
        return "no_video_id (url 파싱 실패)"
    status, reason = plb_map.get(vid, ["?", ""])
    api = api_map.get(vid)

    # ground truth: watch 가 OK 이고 임베드도 허용이면 정상.
    embeddable_ok = (api is None) or (api["embeddable"] is not False)
    if status == "OK" and embeddable_ok:
        return None

    # 원인 보강(우선순위: 삭제 > 임베드차단 > 지역락 > 로그인 > 기타).
    if api is None:
        return f"deleted_or_private (Data API 미응답·영상 없음) [{status}]"
    if api["embeddable"] is False:
        return f"embed_disabled (외부재생 비활성) [{status}]"
    if region_kr_blocked(api["region"]):
        n = len((api["region"].get("blocked") or []))
        return f"region_blocked (KR 지역제한{f', {n}개국 차단' if n else ''}) [{status}]"
    if status == "LOGIN_REQUIRED":
        return f"login_required (연령제한/로그인 필요) [{reason}]"
    if status in ("UNPLAYABLE", "ERROR"):
        return f"unplayable ([{status}] {reason})"
    return f"unknown ([{status}] {reason})"


def main():
    key = load_env_key()
    if not key:
        print("YOUTUBE_API_KEY 없음 (.env 확인)", file=sys.stderr)
        sys.exit(1)

    tracks = load_tracks()
    vids = sorted({r["vid"] for r in tracks if r["vid"]})
    print(f"트랙 {len(tracks)}건 · 고유 video_id {len(vids)}개")

    api_map = fetch_api_status(vids, key)
    print(f"Data API 응답 {len(api_map)}개 (누락 {len(vids) - len(api_map)}개)")
    plb_map = fetch_playability(vids)

    flagged, counts = [], {}
    for r in tracks:
        plb = classify(r, api_map, plb_map)
        if plb:
            counts[plb.split(" ")[0]] = counts.get(plb.split(" ")[0], 0) + 1
            flagged.append((r, plb))

    print("\n=== plb 분류 ===")
    for tag, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {tag:18s}: {n}건")
    print(f"  {'ok(정상)':18s}: {len(tracks) - len(flagged)}건")
    print(f"\n총 재생불가: {len(flagged)}건")

    flagged.sort(key=lambda x: (x[1], x[0]["band"], x[0]["name"]))
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["song_name", "current_url", "modified_url", "plb"])
        for r, plb in flagged:
            w.writerow([r["name"], r["url"], "", plb])
    print(f"저장: {OUT_CSV}  ({len(flagged)}행)")


if __name__ == "__main__":
    main()
