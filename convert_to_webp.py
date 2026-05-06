"""
assets/images/portfolio 配下の PNG/JPG を WebP に一括変換するスクリプト。

- 元ファイルは残し、隣に .webp を生成（非破壊）
- 長辺が MAX_SIDE を超える場合のみ縮小
- すでに新しい .webp があればスキップ
- 並列処理で高速化

使い方: python convert_to_webp.py
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent / "assets" / "images" / "portfolio"
EXTS = {".png", ".jpg", ".jpeg"}
MAX_SIDE = 1600       # 長辺の最大ピクセル
QUALITY = 82          # WebP品質 (0-100)
METHOD = 6            # 圧縮アルゴリズム (0=高速, 6=高圧縮)


def convert_one(src: Path) -> tuple[Path, int, int, str]:
    dst = src.with_suffix(".webp")

    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return src, src.stat().st_size, dst.stat().st_size, "skip"

    try:
        with Image.open(src) as im:
            im.load()
            if im.mode in ("P", "LA"):
                im = im.convert("RGBA")
            elif im.mode == "CMYK":
                im = im.convert("RGB")

            w, h = im.size
            longest = max(w, h)
            if longest > MAX_SIDE:
                scale = MAX_SIDE / longest
                im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

            save_kwargs = {"quality": QUALITY, "method": METHOD}
            if im.mode == "RGBA":
                save_kwargs["lossless"] = False
            im.save(dst, "WEBP", **save_kwargs)
        return src, src.stat().st_size, dst.stat().st_size, "ok"
    except Exception as e:
        return src, 0, 0, f"error: {e}"


def main() -> None:
    if not ROOT.exists():
        print(f"Not found: {ROOT}")
        sys.exit(1)

    targets = [p for p in ROOT.rglob("*") if p.suffix.lower() in EXTS]
    print(f"Targets: {len(targets)} files")

    total_src = 0
    total_dst = 0
    n_ok = n_skip = n_err = 0

    workers = max(1, (os.cpu_count() or 4) - 1)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(convert_one, p): p for p in targets}
        for i, fut in enumerate(as_completed(futures), 1):
            src, s, d, status = fut.result()
            total_src += s
            total_dst += d
            if status == "ok":
                n_ok += 1
            elif status == "skip":
                n_skip += 1
            else:
                n_err += 1
                print(f"  [ERR] {src}: {status}")
            if i % 20 == 0 or i == len(targets):
                print(f"  {i}/{len(targets)}  ok={n_ok} skip={n_skip} err={n_err}")

    mb = lambda b: b / (1024 * 1024)
    print()
    print(f"Done. ok={n_ok} skip={n_skip} err={n_err}")
    print(f"Original total: {mb(total_src):.1f} MB")
    print(f"WebP     total: {mb(total_dst):.1f} MB")
    if total_src:
        print(f"Reduction:      {(1 - total_dst / total_src) * 100:.1f}%")


if __name__ == "__main__":
    main()
