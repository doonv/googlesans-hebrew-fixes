"""Catch the small-size final-kaf/vowel alignment regression."""

from pathlib import Path
import argparse
import io

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from PIL import ImageChops
from hebrew_raster import render_text
from hebrew_shaping import with_original_finalkaf_substitutions


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--font", type=Path, default=Path("out/GoogleSans-HebrewGrade-Prototype.ttf")
)
parser.add_argument(
    "--baseline", type=Path, default=Path("out/GoogleSans-Baseline.ttf")
)
args = parser.parse_args()
path = args.font
data = path.read_bytes()
tt = TTFont(path)
cases = 0
for weight in (400, 500, 600, 700):
    for grade in (0, 100, 200):
        values = {"wght": weight, "GRAD": grade, "opsz": 17}
        font = hb.Font(hb.Face(data))
        font.set_variations(values)
        for text, base, bare in [
            ("ךְ", "uni05DA", "ך"),
            ("ךָ", "uni05DA", "ך"),
            ("ךְּ", "uniFB3A", "ךּ"),
            ("ךָּ", "uniFB3A", "ךּ"),
        ]:
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(font, buf)
            names = [tt.getGlyphOrder()[i.codepoint] for i in buf.glyph_infos]
            assert base in names, (weight, grade, text, names)
            assert len(names) == 2, (text, names)
            for pixels in (12, 14, 16, 20):
                # Compare actual rendered pixels above the baseline, not a
                # glyph loaded twice with identical parameters. The below-base
                # vowel must not shift or change the letter's visible body.
                expected = render_text(path, bare, pixels, values)
                marked = render_text(path, text, pixels, values)
                assert (
                    ImageChops.difference(
                        expected.crop((0, 0, 100, 25)), marked.crop((0, 0, 100, 25))
                    ).getbbox()
                    is None
                ), (path.name, weight, grade, pixels, text)
                cases += 1
print(f"PASS: {cases} marked final-kaf shaping/raster checks")


def positioned_points(data, text, values):
    tt = TTFont(io.BytesIO(data))
    glyphs = tt.getGlyphSet(location=values)
    font = hb.Font(hb.Face(data))
    font.set_variations(values)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer)
    points = []
    cursor = 0
    for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
        pen = DecomposingRecordingPen(glyphs)
        glyphs[tt.getGlyphOrder()[info.codepoint]].draw(pen)
        for _, coords in pen.value:
            points.extend(
                (x + cursor + pos.x_offset, y + pos.y_offset) for x, y in coords
            )
        cursor += pos.x_advance
    return cursor, points


# Check that separate marks occupy the old composites' positions. Compare
# unordered outline points because splitting a composite changes drawing order.
before = with_original_finalkaf_substitutions(data, args.baseline.read_bytes())
max_difference = 0
geometry_cases = 0
for weight in (400, 500, 600, 700):
    for optical_size in (17, 18):
        for grade in (0, 100, 200):
            values = {"wght": weight, "opsz": optical_size, "GRAD": grade}
            for text in ("ךְ", "ךָ", "ךְּ", "ךָּ", "ךְ֑", "ךָ֖"):
                old_advance, old_points = positioned_points(before, text, values)
                new_advance, new_points = positioned_points(data, text, values)
                assert old_advance == new_advance
                assert len(old_points) == len(new_points)
                for source, target in (
                    (old_points, new_points),
                    (new_points, old_points),
                ):
                    difference = max(
                        min(max(abs(x - u), abs(y - v)) for u, v in target)
                        for x, y in source
                    )
                    max_difference = max(max_difference, difference)
                geometry_cases += 1
assert max_difference <= 2, max_difference
print(
    f"PASS: {geometry_cases} positioned-outline checks, unchanged advances; "
    f"maximum point difference {max_difference:.3f}/1000 em"
)
