"""
不足している7カテゴリの画像を、ソースフォルダから直接WebPで取り込む。
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

SRC_BASE = Path(r"C:\Users\misam\OneDrive\デスクトップ\AI関係資料\記憶の保管庫\画像\漫画作品事例")
DST_BASE = Path("assets/images/portfolio")

MISSING = [
    "少年漫画カラータッチ",
    "ミステリアスタッチ2(ベストセラー)",
    "モノクロ青年漫画タッチ(ベストセラー)",
    "モノクロ少年漫画タッチ(受賞)",
    "少年漫画バトルタッチ",
    "墨モノクロ肉質タッチ",
    "水彩タッチ",
]
EXTS = {".png", ".jpg", ".jpeg"}
MAX_SIDE = 1600
QUALITY = 82
METHOD = 6


def convert(args):
    src, dst = args
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return src.name, "skip", 0, 0
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im.load()
            if im.mode in ("P", "LA"):
                im = im.convert("RGBA")
            elif im.mode == "CMYK":
                im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > MAX_SIDE:
                s = MAX_SIDE / max(w, h)
                im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
            kw = {"quality": QUALITY, "method": METHOD}
            if im.mode == "RGBA":
                kw["lossless"] = False
            im.save(dst, "WEBP", **kw)
        return src.name, "ok", src.stat().st_size, dst.stat().st_size
    except Exception as e:
        return src.name, f"err:{e}", 0, 0


def main():
    tasks = []
    for cat in MISSING:
        src_dir = SRC_BASE / cat
        dst_dir = DST_BASE / cat
        if not src_dir.exists():
            print(f"[NOT FOUND] {src_dir}")
            continue
        for src in src_dir.iterdir():
            if src.suffix.lower() in EXTS:
                dst = dst_dir / (src.stem + ".webp")
                tasks.append((src, dst))

    print(f"Targets: {len(tasks)} files")
    total_src = total_dst = 0
    n_ok = n_skip = n_err = 0
    workers = max(1, (os.cpu_count() or 4) - 1)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(convert, t) for t in tasks]
        for i, f in enumerate(as_completed(futs), 1):
            name, st, s, d = f.result()
            total_src += s
            total_dst += d
            if st == "ok":
                n_ok += 1
            elif st == "skip":
                n_skip += 1
            else:
                n_err += 1
                print(f"  [ERR] {name}: {st}")
            if i % 50 == 0 or i == len(tasks):
                print(f"  {i}/{len(tasks)} ok={n_ok} skip={n_skip} err={n_err}")

    mb = lambda b: b / (1024 * 1024)
    print(f"\nDone. ok={n_ok} skip={n_skip} err={n_err}")
    print(f"Source total: {mb(total_src):.1f} MB -> WebP: {mb(total_dst):.1f} MB")


if __name__ == "__main__":
    main()
