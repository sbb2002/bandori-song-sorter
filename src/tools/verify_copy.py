#!/usr/bin/env python3
"""두 폴더의 파일 무결성 비교 (복사/이동 검증용).

사용:
    python src/tools/verify_copy.py <원본폴더> <사본폴더> [--hash]

    예) python src/tools/verify_copy.py src/content/cluster/audio_full "E:/audio_full"
        python src/tools/verify_copy.py src/content/cluster/audio_full "E:/audio_full" --hash

동작:
  - 기본(빠름)      : 하위 파일 이름(상대경로) + 크기 비교. 누락/여분/크기불일치(절단) 탐지.
  - --hash(확실/느림): 크기가 같은 파일에 대해 SHA-256 내용까지 대조. 원본/사본을
                       두 스레드로 동시에 읽어(다른 드라이브라 겹쳐서) 시간을 줄인다.

판정: 누락/크기불일치/내용불일치가 하나도 없으면 OK (사본이 원본을 온전히 포함).
      '여분'(사본에만 있는 파일)은 정보만 표시(무결성 실패 아님).
      종료코드 0=OK / 1=불일치 / 2=사용법오류.
"""
import sys
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# 한국어 Windows 콘솔(cp949)에서 미지원 문자로 죽지 않게: 인코딩은 유지하고 오류만 치환.
try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass


def walk_files(root: Path) -> dict:
    """root 이하 모든 파일 -> {상대경로(슬래시 정규화): Path}."""
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("\\", "/")] = p
    return out


def sha256(path: Path, buf: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_gb(n: int) -> str:
    return f"{n / 1024**3:.2f} GiB"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    do_hash = "--hash" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if len(paths) != 2:
        print(__doc__)
        return 2

    src, dst = Path(paths[0]), Path(paths[1])
    for label, d in (("원본", src), ("사본", dst)):
        if not d.is_dir():
            print(f"[ERROR] {label} 폴더 없음: {d}")
            return 2

    A, B = walk_files(src), walk_files(dst)
    ka, kb = set(A), set(B)
    missing = sorted(ka - kb)     # 사본에 없음(복사 누락)
    extra = sorted(kb - ka)       # 사본에만 있음(정보)
    common = sorted(ka & kb)

    src_bytes = sum(p.stat().st_size for p in A.values())
    mode = "이름+크기+SHA256" if do_hash else "이름+크기(빠름)"
    print(f"원본 {len(A)}개 ({fmt_gb(src_bytes)}) | 사본 {len(B)}개 | 공통 {len(common)} | 모드={mode}")

    size_bad = []
    for k in common:
        sa, sb = A[k].stat().st_size, B[k].stat().st_size
        if sa != sb:
            size_bad.append((k, sa, sb))

    hash_bad = []
    if do_hash:
        # 크기가 맞는 파일만 내용 대조. 원본/사본을 두 스레드로 동시에 읽어 겹침(다른 드라이브).
        good = [k for k in common if A[k].stat().st_size == B[k].stat().st_size]
        total = len(good)
        with ThreadPoolExecutor(max_workers=2) as ex:
            for i, k in enumerate(good, 1):
                fa = ex.submit(sha256, A[k])
                fb = ex.submit(sha256, B[k])
                if fa.result() != fb.result():
                    hash_bad.append(k)
                if i % 20 == 0 or i == total:
                    print(f"  ...해시 {i}/{total}", end="\r", flush=True)
        print()

    def dump(title, items, fmt=lambda x: f"  {x}"):
        print(f"\n[{title} {len(items)}]")
        for it in items[:50]:
            print(fmt(it))
        if len(items) > 50:
            print(f"  ... 외 {len(items) - 50}개")

    if missing:
        dump("누락 - 사본에 없음", missing)
    if size_bad:
        dump("크기불일치(절단 의심)", size_bad,
             lambda t: f"  {t[0]}  원본 {t[1]} vs 사본 {t[2]}")
    if do_hash and hash_bad:
        dump("내용불일치(SHA256)", hash_bad)
    if extra:
        dump("여분 - 사본에만 있음(무결성 무관/정보)", extra)

    fail = bool(missing or size_bad or hash_bad)
    if not fail:
        chk = "이름+크기+SHA256" if do_hash else "이름+크기"
        tail = "" if do_hash else " (내용까지 확인하려면 --hash)"
        print(f"\n[OK] 무결성 OK ({chk}) - 사본이 원본 {len(A)}개 파일을 온전히 포함{tail}")
        return 0
    print("\n[FAIL] 불일치 발견 - 위 목록 확인 후 해당 파일 재복사 요망.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
