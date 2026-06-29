"""assets/lyrics/<band>.md 파서.

가사 .md는 곡마다 다음 구조를 가진다.

    ## N. 곡제목
    - url: ...
    - views: 123,456
    - comment: Cover        (선택 — 커버곡 표시)

    ```
    日本語の原文              <- jp(원문)
    니혼고노 겐분             <- romaji(일어 한글 음차)
    일본어 원문              <- ko(한글 번안)

    次の行 ...
    ```

원문/음차/번안은 줄 단위로 정렬돼 있고 트리플렛 사이는 빈 줄로 구분된다.
다만 영어 단독 줄·의성어 줄 등 번역이 없는 줄도 섞여 있으므로,
빈 줄 묶음에 의존하지 않고 **줄별 문자종(일본어/한글/기타)** 으로 분류한 뒤
"jp 줄 + 뒤따르는 한글 줄들" 을 한 블록으로 묶는 상태기계로 파싱한다.
블록의 마지막 한글 줄 = 번안(ko), 첫 한글 줄 = 음차(romaji).

원문 가사는 보관하지 않는다(저작권). 이 파서의 산출물은 키워드 추출·정렬용
중간 표현일 뿐이며, build_keywords.py 가 단어 단위 키워드만 yaml로 남긴다.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# 일본어: 히라가나·가타카나·한자·반복기호(々〆) · 장음(ー)
_JP = re.compile(r"[぀-ヿ㐀-鿿々〆ｦ-ﾟ]")
# 한글 음절(완성형)
_KO = re.compile(r"[가-힣]")

LINE_JP = "jp"
LINE_KO = "ko"
LINE_OTHER = "other"


def classify(line: str) -> str:
    """줄을 문자종으로 분류. 일본어 우선(원문), 그다음 한글(음차/번안)."""
    if _JP.search(line):
        return LINE_JP
    if _KO.search(line):
        return LINE_KO
    return LINE_OTHER


@dataclass
class Block:
    """jp 원문 한 줄 + 그에 딸린 한글 줄(들)."""
    jp: str
    hangul: list[str] = field(default_factory=list)

    @property
    def translation(self) -> str | None:
        """번안(ko) = 마지막 한글 줄. 음차만 있고 번안이 없을 수 있어 None 가능."""
        return self.hangul[-1] if self.hangul else None


@dataclass
class Song:
    title: str
    url: str = ""
    views: int = 0
    cover: bool = False
    blocks: list[Block] = field(default_factory=list)

    @property
    def has_lyrics(self) -> bool:
        return any(b.jp for b in self.blocks)


def _parse_views(raw: str) -> int:
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else 0


def _parse_fence_blocks(inner: list[str]) -> list[Block]:
    """코드펜스 내부 줄들을 (jp 줄 + 뒤따르는 한글 줄들) 블록으로 묶는다."""
    blocks: list[Block] = []
    cur: Block | None = None
    for raw in inner:
        line = raw.strip()
        if not line:                      # 빈 줄 → 현재 블록 종료
            cur = None
            continue
        kind = classify(line)
        if kind == LINE_JP:
            cur = Block(jp=line)
            blocks.append(cur)
        elif kind == LINE_KO:
            if cur is not None:
                cur.hangul.append(line)
            # 선행 jp 없는 한글 줄(고아) → 무시
        else:                             # 영어/기호 단독 줄 → 블록 경계
            cur = None
    return blocks


def parse_band(path: str | Path) -> list[Song]:
    """<band>.md → Song 리스트."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    songs: list[Song] = []
    cur: Song | None = None
    in_fence = False
    fence_buf: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            cur = Song(title=stripped[3:].strip())
            songs.append(cur)
            in_fence = False
            fence_buf = []
            continue

        if cur is None:
            continue

        if stripped.startswith("```"):
            if in_fence:                  # 펜스 닫힘 → 버퍼 파싱
                cur.blocks.extend(_parse_fence_blocks(fence_buf))
                fence_buf = []
            in_fence = not in_fence
            continue

        if in_fence:
            fence_buf.append(line)
            continue

        # 메타데이터(펜스 밖)
        m = re.match(r"-\s*(url|views|comment)\s*:\s*(.*)", stripped, re.I)
        if m:
            key, val = m.group(1).lower(), m.group(2).strip()
            if key == "url":
                cur.url = val
            elif key == "views":
                cur.views = _parse_views(val)
            elif key == "comment":
                if "cover" in val.lower():
                    cur.cover = True

    return songs


def _selftest(path: str) -> None:
    songs = parse_band(path)
    print(f"# {path}\n곡 {len(songs)}개")
    for i, s in enumerate(songs, 1):
        n_jp = sum(1 for b in s.blocks if b.jp)
        n_tr = sum(1 for b in s.blocks if b.translation)
        flag = " [COVER]" if s.cover else ""
        empty = "" if s.has_lyrics else "  <빈 곡>"
        print(f"{i:2}. {s.title[:30]:30} views={s.views:>9,} "
              f"jp줄={n_jp:>3} 번안={n_tr:>3}{flag}{empty}")
    # 분류 샘플: 첫 곡 앞 3블록의 jp / 음차 / 번안
    first = next((s for s in songs if s.has_lyrics), None)
    if first:
        print("\n[분류 샘플 — 첫 곡 앞 3블록]")
        for b in first.blocks[:3]:
            print(f"  jp  : {b.jp}")
            if len(b.hangul) >= 2:
                print(f"  음차: {b.hangul[0]}")
            print(f"  번안: {b.translation}")
            print()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "assets/lyrics/afterglow.md"
    _selftest(target)
