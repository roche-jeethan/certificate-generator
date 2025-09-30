"""
generate_certificates.py

Usage example:
uv run main.py --x 1000 --y 707
"""

import argparse
import csv
import os
import re
import sys
import tempfile
import zipfile
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except Exception:
    CAIROSVG_AVAILABLE = False


def sanitize_filename(name: str) -> str:
    if not name or not name.strip():
        return "participant"
    s = re.sub(r"\s+", "_", name.strip())
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", s)
    return s[:120] or "participant"


def load_names(path: str):
    names = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='latin-1') as f:
            content = f.read().strip()
    
    if not content:
        return names
    
    lines = content.splitlines()
    has_comma = any(',' in line for line in lines)
    
    if has_comma:
        try:
            reader = csv.reader(lines)
            for row in reader:
                if row:
                    for cell in row:
                        if cell and cell.strip():
                            names.append(cell.strip())
                            break
        except csv.Error:
            for line in lines:
                if line.strip():
                    names.append(line.strip())
    else:
        for line in lines:
            if line.strip():
                names.append(line.strip())
    
    return list(dict.fromkeys(names))


def render_template_to_png_bytes(template_path: str, width: int = None, height: int = None):
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    ext = os.path.splitext(template_path)[1].lower()
    if ext == ".svg":
        if not CAIROSVG_AVAILABLE:
            raise RuntimeError("cairosvg is required to use SVG templates. Install with: pip install cairosvg")
        cairosvg_args = {"background_color": "white"}
        if width and width > 0:
            cairosvg_args["output_width"] = width
        if height and height > 0:
            cairosvg_args["output_height"] = height
        try:
            png_bytes = cairosvg.svg2png(url=template_path, **cairosvg_args)
            if not png_bytes:
                raise RuntimeError("SVG conversion failed")
            return png_bytes
        except Exception as e:
            raise RuntimeError(f"SVG conversion error: {str(e)}")
    else:
        try:
            with open(template_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read template file: {str(e)}")


def draw_name_on_image(img: Image.Image, name: str, x: int, y: int,
                       font: ImageFont.FreeTypeFont, fill: str, align: str = "center",
                       outline: bool = False, outline_width: int = 2):
    if not name or not name.strip():
        return img
    
    draw = ImageDraw.Draw(img)
    name = name.strip()
    
    try:
        bbox = draw.textbbox((0, 0), name, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except Exception:
        try:
            text_w, text_h = draw.textsize(name, font=font)
        except AttributeError:
            text_w = len(name) * (font.size // 2)
            text_h = font.size
    
    if align == "center":
        tx = x - text_w // 2
    elif align == "right":
        tx = x - text_w
    else:
        tx = x
    ty = y - text_h // 2
    
    tx = max(0, min(tx, img.width - text_w))
    ty = max(0, min(ty, img.height - text_h))
    
    if outline and outline_width > 0:
        for ox in range(-outline_width, outline_width + 1):
            for oy in range(-outline_width, outline_width + 1):
                if ox == 0 and oy == 0:
                    continue
                try:
                    draw.text((tx + ox, ty + oy), name, font=font, fill="black")
                except Exception:
                    pass
    
    try:
        draw.text((tx, ty), name, font=font, fill=fill)
    except Exception as e:
        print(f"Warning: Failed to draw text '{name}': {e}", file=sys.stderr)
    
    return img


def main():
    parser = argparse.ArgumentParser(description="Generate certificates from a template and names list.")
    parser.add_argument("--template", "-t", required=False, help="Path to template image (PNG or SVG).")
    parser.add_argument("--names", "-n", required=False, help="Path to names file (CSV or TXT).")
    parser.add_argument("--x", type=int, required=True, help="X coordinate (pixels) for the name anchor.")
    parser.add_argument("--y", type=int, required=True, help="Y coordinate (pixels) for the name anchor.")
    parser.add_argument("--font", "-f", required=False, help="Path to .ttf/.otf font that supports your language.")
    parser.add_argument("--fontsize", required=False, type=int, default=90, help="Font size in points.")
    parser.add_argument("--color", default="#000000", help="Text color (hex or common color names).")
    parser.add_argument("--align", choices=["left", "center", "right"], default="center", help="Text horizontal alignment.")
    parser.add_argument("--out", "-o", default="certificates.zip", help="Output zip filename.")
    parser.add_argument("--outfile_format", default="{name}.png", help="Format string for output files inside zip. Use {name}.")
    parser.add_argument("--outline", action="store_true", help="Draw black outline behind text to improve readability.")
    parser.add_argument("--dpi", type=int, default=600, help="DPI for rendering (affects SVG->PNG quality).")
    args = parser.parse_args()

    template_path = "template.png"
    names_path = "participants.csv"
    font_path = "GoogleSans-Regular.ttf"
    output_zip = "certificates.zip"

    for path, name in [(template_path, "template"), (names_path, "participants file"), (font_path, "font file")]:
        if not os.path.exists(path):
            print(f"ERROR: {name} not found: {path}", file=sys.stderr)
            sys.exit(1)

    try:
        names = load_names(names_path)
    except Exception as e:
        print(f"ERROR: Failed to load names file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not names:
        print("ERROR: No valid names found in the names file.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(names)} names")
    
    try:
        png_bytes = render_template_to_png_bytes(template_path)
    except Exception as e:
        print(f"ERROR: Template processing failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        base_img = Image.open(BytesIO(png_bytes)).convert("RGBA")
    except Exception as e:
        print(f"ERROR: Failed to open template as image: {e}", file=sys.stderr)
        sys.exit(1)
    
    base_width, base_height = base_img.size
    print(f"Template size: {base_width} x {base_height} pixels")
    
    if args.x < 0 or args.x >= base_width or args.y < 0 or args.y >= base_height:
        print(f"WARNING: Coordinates ({args.x}, {args.y}) may be outside image bounds", file=sys.stderr)
    
    try:
        font = ImageFont.truetype(font_path, args.fontsize)
    except Exception as e:
        print(f"ERROR: Failed to load font: {e}", file=sys.stderr)
        try:
            font = ImageFont.load_default()
            print("Using default font as fallback", file=sys.stderr)
        except Exception:
            print("ERROR: No font available", file=sys.stderr)
            sys.exit(1)
    
    out_zip_path = os.path.abspath(output_zip)
    success_count = 0
    
    try:
        with zipfile.ZipFile(out_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for idx, name in enumerate(names, start=1):
                try:
                    safe_name = sanitize_filename(name)
                    out_filename = f"{safe_name}.png"
                    
                    img = base_img.copy()
                    img = draw_name_on_image(img, name, args.x, args.y, font, args.color, 
                                           align="center", outline=args.outline)
                    
                    img_bytes = BytesIO()
                    img.save(img_bytes, format="PNG", optimize=True, dpi=(args.dpi, args.dpi))
                    img_bytes.seek(0)
                    
                    zf.writestr(out_filename, img_bytes.read())
                    success_count += 1
                    print(f"[{idx}/{len(names)}] ✓ {out_filename} (name: {name})")
                    
                except Exception as e:
                    print(f"[{idx}/{len(names)}] ✗ Failed for '{name}': {e}", file=sys.stderr)
                    continue
                    
    except Exception as e:
        print(f"ERROR: Failed to create ZIP file: {e}", file=sys.stderr)
        sys.exit(1)

    if success_count == 0:
        print("ERROR: No certificates were generated successfully", file=sys.stderr)
        sys.exit(1)
    
    print(f"Done. Generated {success_count}/{len(names)} certificates")
    print(f"Certificates ZIP created at: {out_zip_path}")


if __name__ == "__main__":
    main()
