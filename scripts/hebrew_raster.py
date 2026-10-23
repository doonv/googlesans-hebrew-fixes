"""Render HarfBuzz positions through FreeType without rounding glyph origins."""

from pathlib import Path

import freetype
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image


def render_text(
    path, text, pixels, values, *, yod_shift=0, canvas=(100, 50), baseline=(10, 25)
):
    path = Path(path)
    tt = TTFont(path)
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, pixels)
    face.set_var_design_coords([values[a.axisTag] for a in tt["fvar"].axes])
    font = hb.Font(hb.Face(path.read_bytes()))
    font.set_variations(values)
    font.scale = (pixels * 64, pixels * 64)
    font.ppem = (pixels, pixels)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer)
    image = Image.new("RGB", canvas, "#fafafa")
    matrix = freetype.Matrix(65536, 0, 0, 65536)
    cursor = round(baseline[0] * 64)
    yod = tt.getGlyphID("uni05D9")
    for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
        x = (
            cursor
            + pos.x_offset
            + (round(yod_shift * 64) if info.codepoint == yod else 0)
        )
        y = pos.y_offset
        face.set_transform(matrix, freetype.Vector(x % 64, y % 64))
        face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
        bitmap = face.glyph.bitmap
        if bitmap.width and bitmap.rows:
            mask = Image.frombytes(
                "L",
                (bitmap.width, bitmap.rows),
                bytes(bitmap.buffer),
                "raw",
                "L",
                bitmap.pitch,
            )
            image.paste(
                "#111111",
                (
                    x // 64 + face.glyph.bitmap_left,
                    baseline[1] - y // 64 - face.glyph.bitmap_top,
                ),
                mask,
            )
        cursor += pos.x_advance
    return image
