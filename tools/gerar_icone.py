#!/usr/bin/env python3
"""Gera ZeloAppfIco.ico a partir do PNG do logo (fundo escuro vira transparente)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ICO = ROOT / "ZeloAppfIco.ico"
OUT_BUILD = ROOT / "build" / "setup.ico"
SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def _resolver_png() -> Path:
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.is_file():
            return p
    candidatos = [
        ROOT / "ZeloAppfIco.png",
        ROOT / "assets" / "ZeloAppfIco.png",
    ]
    assets = ROOT / "assets"
    if assets.is_dir():
        for p in sorted(assets.glob("ZeloAppfIco*.png")):
            candidatos.append(p)
        for p in sorted(assets.glob("*ZeloAppfIco*.png")):
            candidatos.append(p)
    for c in candidatos:
        if c.is_file():
            return c
    raise SystemExit(
        "PNG não encontrado. Use: python tools/gerar_icone.py caminho\\logo.png\n"
        "Ou copie o logo para ZeloAppfIco.png na raiz do projeto."
    )


def _fundo_transparente(img):
    from PIL import Image

    rgba = img.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r < 40 and g < 40 and b < 40:
                px[x, y] = (r, g, b, 0)
    return rgba


def main() -> None:
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Instale Pillow: pip install pillow")

    src = _resolver_png()
    base = _fundo_transparente(Image.open(src))
    w, h = base.size
    side = max(w, h)
    if w != h:
        sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        sq.paste(base, ((side - w) // 2, (side - h) // 2))
        base = sq

    master = base.resize((256, 256), Image.Resampling.LANCZOS)
    frames = [master.resize(size, Image.Resampling.LANCZOS) for size in SIZES]
    for dest in (OUT_ICO, OUT_BUILD):
        dest.parent.mkdir(parents=True, exist_ok=True)
        frames[0].save(dest, format="ICO", append_images=frames[1:])
    print(f"Ícones gerados: {OUT_ICO} e {OUT_BUILD} (origem: {src})")


if __name__ == "__main__":
    main()
