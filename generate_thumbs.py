"""
script.js の portfolioData から cover URL を抽出し、
それぞれの .webp から 400px幅のサムネイル <name>-thumb.webp を生成する。
"""
import re
import urllib.parse
from pathlib import Path

from PIL import Image

THUMB_WIDTH = 400
QUALITY = 80

def main():
    js_path = Path("assets/js/script.js")
    js = js_path.read_text(encoding="utf-8")
    covers = re.findall(r'"cover":\s*"([^"]+)"', js)

    ok = err = 0
    for url in covers:
        path = Path(urllib.parse.unquote(url))
        webp = path.with_suffix(".webp")
        if not webp.exists():
            print(f"[SKIP] WebP not found: {webp}")
            err += 1
            continue

        thumb = webp.with_name(webp.stem + "-thumb.webp")
        try:
            with Image.open(webp) as im:
                im.load()
                w, h = im.size
                if w > THUMB_WIDTH:
                    scale = THUMB_WIDTH / w
                    im = im.resize((THUMB_WIDTH, int(h * scale)), Image.LANCZOS)
                im.save(thumb, "WEBP", quality=QUALITY, method=6)
            print(f"[OK] {thumb.name}: {webp.stat().st_size:,} -> {thumb.stat().st_size:,}")
            ok += 1
        except Exception as e:
            print(f"[ERR] {webp}: {e}")
            err += 1

    print(f"\nDone. ok={ok} err={err}")

if __name__ == "__main__":
    main()
