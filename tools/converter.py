"""
YAML <-> CSV Converter
Converts between YAML album/track format and flat CSV format.

CSV columns: band, numbering, album_title, img_url, track_number, name, url
"""

import csv
import sys
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)


# ──────────────────────────────────────────────
# YAML → CSV
# ──────────────────────────────────────────────

def yaml_to_csv(yaml_path: str, csv_path: str) -> None:
    """Convert a YAML file to a flat CSV file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        albums = yaml.safe_load(f)

    if not isinstance(albums, list):
        raise ValueError("YAML root must be a list of album objects.")

    fieldnames = ["band", "numbering", "album_title", "img_url", "track_number", "name", "url"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for album in albums:
            band        = album.get("band", "")
            numbering   = album.get("numbering", "")
            album_title = album.get("album_title", "")
            img_url     = album.get("img_url", "")
            tracks      = album.get("tracks", [])

            for track in tracks:
                writer.writerow({
                    "band":         band,
                    "numbering":    numbering,
                    "album_title":  album_title,
                    "img_url":      img_url,
                    "track_number": track.get("track_number", ""),
                    "name":         track.get("name", ""),
                    "url":          track.get("url", ""),
                })

    print(f"[yaml→csv] Done: {csv_path}")


# ──────────────────────────────────────────────
# CSV → YAML
# ──────────────────────────────────────────────

def csv_to_yaml(csv_path: str, yaml_path: str) -> None:
    """Convert a flat CSV file back to the nested YAML format."""

    # Columns that belong to the album level (not tracks)
    ALBUM_FIELDS = {"band", "numbering", "album_title", "img_url"}

    albums: list[dict] = []
    album_index: dict[tuple, int] = {}  # (band, numbering, album_title, img_url) → index in albums

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Determine which columns are extra (not album-level) — these all go into tracks
        all_columns = reader.fieldnames or []
        track_fields = [c for c in all_columns if c not in ALBUM_FIELDS]

        for row in reader:
            key = (
                row.get("band", ""),
                row.get("numbering", ""),
                row.get("album_title", ""),
                row.get("img_url", ""),
            )

            if key not in album_index:
                album_index[key] = len(albums)
                albums.append({
                    "band":        row.get("band", ""),
                    "numbering":   row.get("numbering", ""),
                    "album_title": row.get("album_title", ""),
                    "img_url":     row.get("img_url", ""),
                    "tracks":      [],
                })

            # All non-album columns go into the track entry (including any extras)
            track_entry = {field: row.get(field, "") for field in track_fields}
            albums[album_index[key]]["tracks"].append(track_entry)

    # Custom YAML dumper to match the original style
    class QuotedStr(str):
        pass

    def quoted_str_representer(dumper, data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")

    # Fields that should always be single-quoted
    QUOTED_TRACK_FIELDS = {"track_number", "name"}
    QUOTED_ALBUM_FIELDS = {"band", "numbering", "album_title"}

    def album_to_ordereddict(album, extra_track_fields: list[str]):
        """Return a plain dict that preserves key order for yaml.dump."""
        result = {}
        for k in ["band", "numbering", "album_title", "img_url"]:
            result[k] = QuotedStr(album[k]) if k in QUOTED_ALBUM_FIELDS else album[k]

        def build_track(t):
            entry = {}
            for field in track_fields:
                val = t.get(field, "")
                entry[field] = QuotedStr(val) if field in QUOTED_TRACK_FIELDS else val
            return entry

        result["tracks"] = [build_track(t) for t in album["tracks"]]
        return result

    dumper = yaml.Dumper
    dumper.add_representer(QuotedStr, quoted_str_representer)

    output = yaml.dump(
        [album_to_ordereddict(a, track_fields) for a in albums],
        Dumper=dumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
    )

    # yaml.dump uses "- " at the same indent as its parent; adjust list items
    # so top-level list entries are separated by a blank line for readability.
    lines = output.splitlines()
    pretty_lines = []
    for i, line in enumerate(lines):
        if line.startswith("- band:") and i != 0:
            pretty_lines.append("")  # blank line between albums
        pretty_lines.append(line)

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(pretty_lines) + "\n")

    print(f"[csv→yaml] Done: {yaml_path}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def usage():
    print(
        "Usage:\n"
        "  yaml→csv:  python yaml_csv_converter.py yaml2csv <input.yaml> [output.csv]\n"
        "  csv→yaml:  python yaml_csv_converter.py csv2yaml <input.csv>  [output.yaml]"
    )


def main():
    if len(sys.argv) < 3:
        usage()
        sys.exit(1)

    mode      = sys.argv[1].lower()
    input_path = sys.argv[2]

    if mode == "yaml2csv":
        output_path = sys.argv[3] if len(sys.argv) > 3 else Path(input_path).with_suffix(".csv")
        yaml_to_csv(input_path, str(output_path))

    elif mode == "csv2yaml":
        output_path = sys.argv[3] if len(sys.argv) > 3 else Path(input_path).with_suffix(".yaml")
        csv_to_yaml(input_path, str(output_path))

    else:
        print(f"Unknown mode: {mode!r}")
        usage()
        sys.exit(1)


if __name__ == "__main__":
    main()