"""assets/lyrics/<band>.md → wordcloud/<band>.yaml 키워드 추출 파이프라인.

결정(2026-06-26 ②안 + 2026-06-27 사용자 지시):
  - 일본어 원문에서 **명사**만 추출(fugashi + unidic-lite), 빈도 집계.
  - **커버곡 제외**(밴드 고유 정체성 기준; comment: Cover 표시 활용).
  - 한국어(ko)는 가사에 함께 있는 **한글 번안**을 통계적 단어정렬로 추정.
    정렬이 약하거나 번안이 없는 명사는 **기계번역(deep-translator)** 으로 보완,
    그래도 못 채우면 빈칸(사용자 직접 입력).
  - 산출물 yaml은 **단어 단위 키워드 + 빈도만** 보관(가사 원문 미보관 → 저작권 회피).

스키마(밴드별):
    band: <name>
    generated: 'YYYY-MM-DD'
    song_count: <키워드 산출에 쓰인 곡 수(커버 제외)>
    keywords:
      - {jp: 世界, ko: 세계, weight: 5}     # 정렬/번역 출처는 eol 주석으로 표기

사용:
    python src/tools/wordcloud/build_keywords.py            # 전 밴드 → wordcloud/*.yaml
    python src/tools/wordcloud/build_keywords.py --debug    # yaml 미기록, 상위 명사만 출력
    python src/tools/wordcloud/build_keywords.py --no-translate   # 기계번역 보완 끔
    python src/tools/wordcloud/build_keywords.py --band afterglow # 특정 밴드만
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fugashi  # noqa: E402
from kiwipiepy import Kiwi  # noqa: E402
from lyrics_parser import parse_band, Song  # noqa: E402
from kana2ko import kana2ko, CHO, JUNG, JONG  # noqa: E402

# 가나전용(가타카나/히라가나/장음/중점) 토큰 — 보컬리제·외래어 음차 후보.
_KANA_ONLY = re.compile(r"^[぀-ゟ゠-ヿ・]+$")
# 한국어 결과에 일본어(가나/한자)가 남았는지 — MT 실패(永劫→永劫 등) 감지용.
_HAS_JP = re.compile(r"[぀-ゟ゠-ヿ㐀-鿿々]")
# 가나전용 토큰의 align값이 음차와 이만큼도 안 닮으면 오정렬로 보고 음차로 대체.
_PHON_SIM = 0.5
# align(Dice 단어정렬) 채택 최소 신뢰도. 낮으면 N:1 오정렬↑, 높이면 직역(MT)↑.
_ALIGN_MIN = 0.45

# 수동 교정 사전(최우선·멱등). 영어 외래어는 일본식 음차 대신 한국 표준표기,
# align 통계가 크게 빗나간 항목(jp와 무관한 매핑)을 바로잡는다. 재생성에도 유지됨.
OVERRIDE = {
    # 영어 외래어 → 한국 표준 외래어 표기
    "チャンス": "찬스", "メリーゴーランド": "메리고라운드", "アブラカタブラ": "아브라카타브라",
    "ライフ": "라이프", "タイプ": "타입", "ワールド": "월드", "ワイド": "와이드",
    "ビューティー": "뷰티", "シーフ": "시프", "ファントム": "팬텀",
    "ミュージック": "뮤직", "キズナミュージック": "키즈나뮤직",
    "アップ": "업", "ヤダ": "싫어",
    # 음차로 깨진 영어 외래어 → 표준 표기(2026-06-30 검수)
    "テンション": "텐션", "モブ": "모브", "リズム": "리듬", "リメーク": "리메이크",
    "バーチャル": "버추얼", "フィクション": "픽션", "ノンフィクション": "논픽션",
    "ミュータント": "뮤턴트", "パワー": "파워", "フリー": "프리", "チート": "치트",
    "オルターナティブ": "얼터너티브", "メンバー": "멤버", "シャウト": "샤우트",
    "チャレンジ": "챌린지", "マーチング": "마칭", "バトン": "바통", "ニヒル": "니힐",
    "アンサー": "앤서", "ステレオタイプ": "스테레오타입", "フィフティー": "피프티",
    "パーリー": "파티", "フェスティバル": "페스티벌",
    # align 대형 오정렬 교정(jp와 무관·여러 jp가 한 ko로 N:1 붕괴)
    "縁": "인연", "婆": "할멈", "仕様": "사양", "以上": "이상", "回転": "회전",
    "赤": "빨강", "象": "코끼리", "獅子": "사자", "瞬き": "깜빡임", "禁止": "금지",
    "熊": "곰", "身体": "몸", "宝石": "보석", "香り": "향기", "自ら": "스스로",
    "格好": "모습", "事実": "사실", "関係": "관계", "探し": "찾기", "果て": "끝",
    "曲": "곡", "真っ盛り": "한창", "模様": "무늬", "法被": "핫피",
}


def _jamo(s: str) -> list[str]:
    """한글 음절열을 초성·중성·종성 자모 시퀀스로 분해(유사도 비교용)."""
    out: list[str] = []
    for ch in s:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3:
            b = o - 0xAC00
            out.append(CHO[b // 588])
            out.append(JUNG[(b % 588) // 28])
            t = b % 28
            if t:
                out.append(JONG[t])
        else:
            out.append(ch)
    return out


def _phon_similar(a: str, b: str) -> float:
    """두 한글 표기의 자모 시퀀스 유사도(0~1)."""
    return difflib.SequenceMatcher(None, _jamo(a), _jamo(b)).ratio()


def resolve_ko(jp: str, align: dict[str, str], translate):
    """jp 명사 → (ko, 출처). OVERRIDE→align→음차→MT→빈칸. 가나전용은 align 오정렬을 음차로 교정."""
    if jp in OVERRIDE:
        return OVERRIDE[jp], "align"        # 수동 교정(외래어 표준표기·대형 오정렬)
    is_kana = bool(_KANA_ONLY.match(jp))
    if jp in align:
        if is_kana:
            phon = kana2ko(jp)
            # align값이 음차와 딴판이거나 음차의 부분조각처럼 너무 짧으면 음차로 교체
            if _phon_similar(align[jp], phon) < _PHON_SIM or len(align[jp]) < 0.6 * len(phon):
                return phon, "kana"
        return align[jp], "align"
    if is_kana:
        return kana2ko(jp), "kana"          # 보컬리제·의성어 → 음차
    if translate:
        ko = translate(jp)
        if ko and not _HAS_JP.search(ko):   # MT에 일본어 잔존 시 거부 → 빈칸
            return ko, "mt"
    return "", "none"

LYRICS_DIR = Path("assets/lyrics")
OUT_DIR = Path("src/content/wordcloud")

# ── 명사 필터 ───────────────────────────────────────────────────────────────
# 기능성·약한 명사(형식명사, 시공간 일반어 등)는 테마성이 낮아 제외.
STOPWORDS = {
    "事", "物", "者", "為", "様", "所", "方", "中", "内", "際", "等", "度",
    "今", "時", "日", "共", "何", "うち", "わけ", "はず", "つもり", "とこ",
    "そう", "よう", "ふう", "みたい", "やつ", "とき", "ところ", "もの", "こと",
    "侭", "儘", "まま", "やつ", "筈", "訳", "故", "由", "旨", "序で",
    "ん", "の", "さ", "ーー", "・",
    "取り", "通り",                       # 동사연용·형식명사("~취함"·"~대로") — 테마성 무
    # 보컬리제·기능어 단편(분해 오류·의미불명 — 사용자 검수 2026-06-27)
    "ケン", "ソウ", "メイ", "ラン", "ワン", "ココ", "イズ", "モリ",
    "フォー", "ユー", "ミー", "フォーミー", "合", "対",
    # 복합어·사자성어 분해조각, 방향·횟수 일반어(추가 검수 2026-06-30)
    "実", "感", "図", "羅", "芒", "只", "重", "精", "上", "下", "回", "倍",
}
# pos1/pos2 화이트리스트
_KEEP_POS2 = {"普通名詞", "固有名詞"}
_LATIN = re.compile(r"^[A-Za-z0-9·・\-'’\s]+$")
_KANA1 = re.compile(r"^[぀-ヿ]$")          # 길이 1 가나(한자 제외) → 노이즈

_tagger = fugashi.Tagger()


def _lemma_base(word) -> str:
    """unidic lemma에서 외래어 '-romaji' 접미를 떼고 표제형을 얻는다."""
    f = word.feature
    lemma = getattr(f, "lemma", None)
    if not lemma or lemma in ("*", ""):
        return word.surface
    # 'メッセージ-message' / 'バイ-by' → 'メッセージ' / 'バイ'
    return lemma.split("-", 1)[0]


def iter_nouns(text: str):
    """일본어 한 줄에서 키워드 후보 명사(표제형)를 순서대로 yield."""
    for w in _tagger(text):
        f = w.feature
        if f.pos1 != "名詞" or f.pos2 not in _KEEP_POS2:
            continue
        base = _lemma_base(w)
        if base in STOPWORDS:
            continue
        if _LATIN.match(base):            # 영어 가사 조각·숫자 제외
            continue
        if _KANA1.match(base):            # 단일 가나 노이즈 제외
            continue
        yield base


# ── 추출 ────────────────────────────────────────────────────────────────────
def extract_band(songs: list[Song], include_covers: bool):
    """(빈도 Counter, 정렬용 (명사집합, 번안문) 리스트, 곡수) 반환."""
    freq: collections.Counter[str] = collections.Counter()
    align_pairs: list[tuple[set[str], str]] = []
    used = 0
    for s in songs:
        if s.cover and not include_covers:
            continue
        if not s.has_lyrics:
            continue
        used += 1
        for b in s.blocks:
            nouns = list(iter_nouns(b.jp))
            for n in nouns:
                freq[n] += 1
            if nouns and b.translation:
                align_pairs.append((set(nouns), b.translation))
    return freq, align_pairs, used


# ── 통계적 단어 정렬(일본어 명사 → 한국어 명사) ───────────────────────────────
# 한국어 형태소 분석(kiwipiepy)으로 번안문에서 **명사만** 뽑아 정렬 정밀도를 높인다.
# (조사 수동 제거 대신 분석기가 명사/동사/부사를 구분 → 동사·부사 오결합 방지.)
_kiwi = Kiwi()
_KO_NOUN_TAGS = ("NNG", "NNP")            # 일반명사·고유명사
# 감탄사/추임새가 명사로 오태깅돼 정렬에 끼는 것 방지(아아아·오오 등).
_KO_NOUN_STOP = {"아", "오", "우", "어", "에", "으", "음", "응", "야", "와", "워"}


def _ko_words(sentence: str) -> set[str]:
    """번안문에서 한국어 명사 집합을 추출."""
    return {t.form for t in _kiwi.tokenize(sentence)
            if t.tag in _KO_NOUN_TAGS and t.form not in _KO_NOUN_STOP}


def build_alignment(all_pairs: list[tuple[set[str], str]]) -> dict[str, str]:
    """전 밴드 (명사집합, 번안문) 쌍에서 Dice 계수로 jp명사→ko단어 표를 만든다."""
    jp_cnt: collections.Counter[str] = collections.Counter()
    ko_cnt: collections.Counter[str] = collections.Counter()
    co: collections.defaultdict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    for nouns, sent in all_pairs:
        kos = _ko_words(sent)
        for j in nouns:
            jp_cnt[j] += 1
            for k in kos:
                co[j][k] += 1
        for k in kos:
            ko_cnt[k] += 1

    table: dict[str, str] = {}
    for j, kcnts in co.items():
        best_k, best_score = None, 0.0
        for k, c in kcnts.items():
            if c < 2:                     # 최소 2회 공기(共起) — 우연 배제
                continue
            if len(k) > 6:                # 비정상 장음절 토큰만 거부(명사 분석 후라 여유)
                continue
            dice = 2 * c / (jp_cnt[j] + ko_cnt[k])
            if dice > best_score:
                best_k, best_score = k, dice
        if best_k and best_score >= _ALIGN_MIN:  # 신뢰도 임계(낮으면 N:1 오정렬↑)
            table[j] = best_k
    return table


# ── 기계번역 보완(선택) ──────────────────────────────────────────────────────
def make_translator(enabled: bool):
    if not enabled:
        return None
    try:
        from deep_translator import GoogleTranslator
    except Exception:
        print("  ! deep-translator 미설치 — 기계번역 보완 생략(ko 빈칸)", file=sys.stderr)
        return None
    tr = GoogleTranslator(source="ja", target="ko")
    cache: dict[str, str] = {}

    def translate(jp: str) -> str:
        if jp in cache:
            return cache[jp]
        try:
            res = (tr.translate(jp) or "").strip()
        except Exception as e:
            print(f"  ! 번역 실패({jp}): {e}", file=sys.stderr)
            res = ""
        cache[jp] = res
        return res

    return translate


# ── yaml 기록 ────────────────────────────────────────────────────────────────
def write_yaml(band: str, freq: collections.Counter, ko_map: dict[str, tuple[str, str]],
               song_count: int, min_weight: int) -> Path:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    items = [(w, c) for w, c in freq.most_common() if c >= min_weight]
    seq = CommentedSeq()
    for i, (jp, weight) in enumerate(items):
        ko, src = ko_map.get(jp, ("", "none"))
        m = CommentedMap([("jp", jp), ("ko", ko), ("weight", weight)])
        m.fa.set_flow_style()
        seq.append(m)
        note = {"align": None, "kana": "음차", "mt": "기계번역 초안",
                "none": "번역 필요"}[src]
        if note:
            seq.yaml_add_eol_comment(note, i)

    doc = CommentedMap([
        ("band", band),
        ("generated", _dt.date.today().isoformat()),
        ("song_count", song_count),
        ("keywords", seq),
    ])
    header = (
        "# 자동 생성 — 일본어 가사 명사 빈도(커버 제외). 가사 원문은 미보관.\n"
        "# ko: 한글 번안 정렬 추정 → 기계번역(주석 표시) → 빈칸 순. 직접 수정·덮어쓰세요.\n"
        "# weight: 원문 등장 빈도(후렴 반복 포함, 렌더에서 압축 가능).\n"
    )
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"{band}.yaml"
    yaml = YAML()
    yaml.allow_unicode = True
    yaml.indent(sequence=2, offset=0)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(header)
        yaml.dump(doc, f)
    return out


# ── 오케스트레이션 ───────────────────────────────────────────────────────────
def band_files(only: str | None) -> list[Path]:
    files = sorted(p for p in LYRICS_DIR.glob("*.md")
                   if not p.stem.endswith("_template"))
    if only:
        files = [p for p in files if p.stem == only]
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", help="특정 밴드만(파일 stem)")
    ap.add_argument("--debug", action="store_true", help="yaml 미기록, 상위 명사만 출력")
    ap.add_argument("--no-translate", dest="translate", action="store_false",
                    help="기계번역 보완 끔")
    ap.add_argument("--include-covers", action="store_true", help="커버곡도 집계")
    ap.add_argument("--min-weight", type=int, default=2,
                    help="이 빈도 미만 제외(기본 2 — 단발성 명사 노이즈 컷)")
    ap.add_argument("--top", type=int, default=40, help="--debug 시 출력 개수")
    args = ap.parse_args(argv)

    files = band_files(args.band)
    if not files:
        print("대상 가사 파일 없음", file=sys.stderr)
        return 1

    parsed = {p.stem: parse_band(p) for p in files}

    # 정렬표는 전 밴드 쌍을 모아 한 번에 구축(데이터 많을수록 정확).
    all_pairs: list[tuple[set[str], str]] = []
    band_freq: dict[str, collections.Counter] = {}
    band_used: dict[str, int] = {}
    for band, songs in parsed.items():
        freq, pairs, used = extract_band(songs, args.include_covers)
        band_freq[band] = freq
        band_used[band] = used
        all_pairs.extend(pairs)

    align = build_alignment(all_pairs)

    if args.debug:
        for band in parsed:
            freq = band_freq[band]
            print(f"\n=== {band} (곡 {band_used[band]}) — 명사 TOP{args.top} ===")
            for jp, c in freq.most_common(args.top):
                ko = align.get(jp, "")
                tag = "  →정렬" if jp in align else ""
                print(f"{c:>3}  {jp:12} {ko}{tag}")
        return 0

    translate = make_translator(args.translate)
    for band in parsed:
        freq = band_freq[band]
        kept = [jp for jp, c in freq.items() if c >= args.min_weight]
        ko_map: dict[str, tuple[str, str]] = {}
        for jp in kept:                   # min_weight 이상만 번역(MT 호출 절감)
            ko_map[jp] = resolve_ko(jp, align, translate)
        out = write_yaml(band, freq, ko_map, band_used[band], args.min_weight)
        n_align = sum(1 for jp in kept if ko_map[jp][1] == "align")
        n_kana = sum(1 for jp in kept if ko_map[jp][1] == "kana")
        n_mt = sum(1 for jp in kept if ko_map[jp][1] == "mt")
        print(f"[OK] {out}  키워드 {len(kept)}  (정렬 {n_align} · 음차 {n_kana} · "
              f"기계번역 {n_mt} · 빈칸 {len(kept) - n_align - n_kana - n_mt})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
