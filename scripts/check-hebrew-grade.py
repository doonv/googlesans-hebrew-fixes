"""Check layout invariance and render a comparison of the experimental grade."""

import argparse
import json
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from PIL import Image, ImageDraw, ImageFont
from ufoLib2 import Font
from hebrew_shaping import without_finalkaf_vowel_ligatures


OUT = Path("out")
BASELINE = OUT / "GoogleSans-Baseline.ttf"
PROTOTYPE = OUT / "GoogleSans-HebrewGrade-Prototype.ttf"
SAMPLES = [
    "אבגדהוזחטיךכלםמןנסעףפץצקרשת",
    "יום ראשון יום שני יום שלישי יום רביעי יום חמישי יום שישי",
    "השיעור הבא: מתמטיקה בכיתה 204",
    "שָׁלוֹם עוֹלָם בְּרֵאשִׁית בָּרָא",
    "שׁ שׂ שּׁ שּׂ בּ כּ פּ ךְ ךָ לֹ לֹּ",
    "עִבְרִית English 123 חיפוש",
    "וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר",
]


def shape(data, text, weight, size, grade, kern=True):
    font = hb.Font(hb.Face(data))
    font.set_variations({"wght": weight, "opsz": size, "GRAD": grade})
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer, {"kern": kern})
    return [
        (i.codepoint, i.cluster, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
        for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", type=int, choices=range(1, 9), default=1)
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Run checks without creating a specimen",
    )
    args = parser.parse_args()
    scale = args.scale
    # Normalize only the four intentionally removed substitutions. All other
    # baseline shaping, outlines and metrics remain the original reference.
    baseline = without_finalkaf_vowel_ligatures(BASELINE.read_bytes())
    prototype = PROTOTYPE.read_bytes()
    cases = 0
    for weight in (400, 500, 600, 700):
        for size in (17, 18):
            for text in SAMPLES:
                # Original pair spacing has been restored. Keep kerning enabled
                # so an accidental spacing change is a real regression.
                before = shape(baseline, text, weight, size, 0)
                zero = shape(prototype, text, weight, size, 0)
                assert before == zero, ("grade-zero regression", weight, size, text)
                for grade in (50, 100, 150, 200):
                    graded = shape(prototype, text, weight, size, grade)
                    # Mark offsets may change intentionally, but glyph selection,
                    # clusters, and advances must not. Kerning is included here.
                    assert [g[:4] for g in graded] == [g[:4] for g in zero], (
                        "layout changed",
                        weight,
                        size,
                        grade,
                        text,
                    )
                    cases += 1

    f = TTFont(PROTOTYPE)
    cmap = f.getBestCmap()
    for code in range(0x5D0, 0x5EB):
        name = cmap[code]
        assert any("GRAD" in v.axes for v in f["gvar"].variations[name]), name

    ink_increase = []
    for size in (17, 18):
        regular = Font.open(f"sources/GoogleSans-opsz{size}-wght380-GRAD0.ufo")
        graded = Font.open(f"sources/GoogleSans-opsz{size}-wght380-GRAD200.ufo")
        letters = [
            n
            for n in regular.keys()
            if any(0x5D0 <= code <= 0x5EA for code in regular[n].unicodes)
        ]
        for name in letters:
            original_area = AreaPen(regular)
            graded_area = AreaPen(graded)
            regular[name].draw(original_area)
            graded[name].draw(graded_area)
            ratio = abs(graded_area.value / original_area.value)
            assert ratio > 1, ("letter did not thicken", size, name)
            assert regular[name].width == graded[name].width
            ink_increase.append(ratio - 1)

    if not args.no_render:
        render_comparison(scale)
    report = {
        "layout_checks_passed": cases,
        "grade_zero_matches_baseline_after_finalkaf_shaping_fix": True,
        "all_27_hebrew_letters_have_grade_deltas": True,
        "weights": [400, 500, 600, 700],
        "optical_sizes": [17, 18],
        "grades": [50, 100, 150, 200],
        "grade_200_letter_ink_increase": [min(ink_increase), max(ink_increase)],
        "limitations": "Desktop validation only; no Android validation or type-design certification.",
    }
    (OUT / "hebrew-grade-checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def render_comparison(scale):
    # Render with RAQM so Hebrew and combining marks are actually shaped.
    image = Image.new("RGB", (1800 * scale, 2000 * scale), "#fafafa")
    draw = ImageDraw.Draw(image)
    label_font = ImageFont.truetype(str(PROTOTYPE), 20 * scale)
    draw.text(
        (30 * scale, 20 * scale),
        "Experimental Hebrew grade | same advances, weight-derived outlines",
        font=label_font,
        fill="black",
    )
    y = 65
    for weight in (400, 700):
        for grade in (0, 100, 200):
            draw.text(
                (30 * scale, y * scale),
                f"wght {weight}, GRAD {grade}",
                font=label_font,
                fill="#555555",
            )
            y += 35
            font = ImageFont.truetype(str(PROTOTYPE), 36 * scale)
            axes = TTFont(PROTOTYPE)["fvar"].axes
            values = {"wght": weight, "opsz": 18, "GRAD": grade}
            font.set_variation_by_axes([values[a.axisTag] for a in axes])
            for text in SAMPLES[:4]:
                draw.text(
                    (1750 * scale, y * scale),
                    text,
                    anchor="rt",
                    direction="rtl",
                    font=font,
                    fill="#111111",
                )
                y += 55
            y += 25
    suffix = f"@{scale}x" if scale != 1 else ""
    comparison = OUT / f"hebrew-grade-comparison{suffix}.png"
    image.crop((0, 0, 1800 * scale, (y + 20) * scale)).save(comparison)
    print(f"Rendered {comparison}: {1800 * scale} x {(y + 20) * scale}")


if __name__ == "__main__":
    main()
