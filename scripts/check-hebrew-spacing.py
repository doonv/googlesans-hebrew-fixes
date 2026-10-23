"""Guard original Hebrew pair spacing after the withdrawn yod experiments."""

from pathlib import Path
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from hebrew_shaping import without_finalkaf_vowel_ligatures


baseline = without_finalkaf_vowel_ligatures(
    Path("out/GoogleSans-Baseline.ttf").read_bytes()
)
current = Path("out/GoogleSans-HebrewGrade-Prototype.ttf").read_bytes()
tt = TTFont("out/GoogleSans-HebrewGrade-Prototype.ttf")
mark_ids = {
    tt.getGlyphID(name)
    for name, category in tt["GDEF"].table.GlyphClassDef.classDefs.items()
    if category == 3
}
texts = ("יש", "יִשׁ", "ישׂ", "יּשּׁ", "יּשּׂ", "שי", "י ש", "מרגיש", "מַרְגִּישׁ", "גיש", "גּיּשּׁ")


def shape(data, text, values):
    font = hb.Font(hb.Face(data))
    font.set_variations(values)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer)
    return [
        # Marks intentionally change position with grade; pair spacing and
        # base-letter positions must remain upstream-compatible.
        (
            i.codepoint,
            i.cluster,
            p.x_advance,
            p.y_advance,
            p.x_offset if i.codepoint not in mark_ids else None,
            p.y_offset if i.codepoint not in mark_ids else None,
        )
        for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)
    ]


cases = 0
for weight in (400, 500, 600, 700):
    for grade in (-50, 0, 100, 200):
        for size in (17, 17.5, 18):
            values = {"wght": weight, "GRAD": grade, "opsz": size}
            for text in texts:
                assert shape(baseline, text, values) == shape(current, text, values), (
                    text,
                    values,
                )
                cases += 1
print(
    f"PASS: {cases} original-spacing checks, including glyph positions and marked forms"
)
