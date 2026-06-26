"""
YAML <-> CSV Converter
Converts between YAML album/track format and flat CSV format.

CSV columns: band, numbering, album_title, img_url, track_number, name, url, [extra track fields...]

Extra track-level fields (e.g. release_date) are preserved automatically:
they appear as additional CSV columns after `url`, and round-trip back into
the YAML tracks. Empty optional fields are omitted from the YAML so existing
data is not polluted with blank keys.
"""

import csv
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)


# ──────────────────────────────────────────────
# Schema
# ──────────────────────────────────────────────

# Album-level columns; every other CSV column belongs to a track.
ALBUM_FIELDS = ["band", "numbering", "album_title", "img_url"]

# Track columns that always exist and are always written (even when empty).
# Any other track keys (e.g. release_date) are treated as optional metadata:
# discovered dynamically, appended after these, and omitted when empty.
BASE_TRACK_FIELDS = ["track_number", "name", "url"]


# ──────────────────────────────────────────────
# YAML → CSV
# ──────────────────────────────────────────────

def yaml_to_csv(yaml_path: str, csv_path: str) -> None:
    """Convert a YAML file to a flat CSV file.

    Track columns are discovered dynamically: the base columns
    (track_number, name, url) come first, then any extra track keys
    (e.g. release_date) in first-seen order, so new metadata is never dropped.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        albums = yaml.safe_load(f)

    if not isinstance(albums, list):
        raise ValueError("YAML root must be a list of album objects.")

    # Discover extra track fields (anything beyond the base set), first-seen order.
    extra_track_fields: list[str] = []
    for album in albums:
        for track in (album.get("tracks") or []):
            for key in track:
                if key not in BASE_TRACK_FIELDS and key not in extra_track_fields:
                    extra_track_fields.append(key)

    track_fields = BASE_TRACK_FIELDS + extra_track_fields
    fieldnames = ALBUM_FIELDS + track_fields

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for album in albums:
            album_cells = {k: album.get(k, "") for k in ALBUM_FIELDS}
            for track in (album.get("tracks") or []):
                row = dict(album_cells)
                for field in track_fields:
                    value = track.get(field, "")
                    row[field] = "" if value is None else value
                writer.writerow(row)

    print(f"[yaml→csv] Done: {csv_path}")


# ──────────────────────────────────────────────
# CSV → YAML
# ──────────────────────────────────────────────

def csv_to_yaml(csv_path: str, yaml_path: str) -> None:
    """Convert a flat CSV file back to the nested YAML format."""

    album_key_fields = set(ALBUM_FIELDS)

    albums: list[dict] = []
    album_index: dict[tuple, int] = {}  # album identity → index in albums

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        all_columns = reader.fieldnames or []
        # Every non-album column is a track field (base + any extras like release_date).
        track_fields = [c for c in all_columns if c not in album_key_fields]

        for row in reader:
            key = tuple(row.get(k, "") for k in ALBUM_FIELDS)

            if key not in album_index:
                album_index[key] = len(albums)
                albums.append({
                    **{k: row.get(k, "") for k in ALBUM_FIELDS},
                    "tracks": [],
                })

            track_entry = {field: row.get(field, "") for field in track_fields}
            albums[album_index[key]]["tracks"].append(track_entry)

    # ----- Custom YAML dumper to match the original style -----
    class QuotedStr(str):
        pass

    def quoted_str_representer(dumper, data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")

    # Always single-quote these so values stay strings
    # (e.g. dates like '2026-06-20', leading-zero track numbers like '01').
    QUOTED_ALBUM_FIELDS = {"band", "numbering", "album_title"}
    QUOTED_TRACK_FIELDS = {"track_number", "name", "release_date"}

    # Required track fields are always emitted; optional ones are dropped when empty
    # so existing tracks aren't littered with blank metadata keys.
    required_track_fields = set(BASE_TRACK_FIELDS)

    def build_track(track):
        entry = {}
        for field in track_fields:
            value = track.get(field, "")
            if field not in required_track_fields and (value is None or value == ""):
                continue  # don't pollute tracks with empty optional metadata
            entry[field] = QuotedStr(value) if field in QUOTED_TRACK_FIELDS else value
        return entry

    def album_to_ordereddict(album):
        """Return a plain dict that preserves key order for yaml.dump."""
        result = {}
        for k in ALBUM_FIELDS:
            result[k] = QuotedStr(album[k]) if k in QUOTED_ALBUM_FIELDS else album[k]
        result["tracks"] = [build_track(t) for t in album["tracks"]]
        return result

    dumper = yaml.Dumper
    dumper.add_representer(QuotedStr, quoted_str_representer)

    output = yaml.dump(
        [album_to_ordereddict(a) for a in albums],
        Dumper=dumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
    )

    # yaml.dump packs list items tightly; insert a blank line between top-level
    # album entries for readability (matches the hand-authored data style).
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
        "  yaml→csv:  python converter.py yaml2csv <input.yaml> [output.csv]\n"
        "  csv→yaml:  python converter.py csv2yaml <input.csv>  [output.yaml]"
    )


def main():
    if len(sys.argv) < 3:
        usage()
        sys.exit(1)

    mode       = sys.argv[1].lower()
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
