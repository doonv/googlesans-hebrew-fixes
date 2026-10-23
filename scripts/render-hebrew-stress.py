"""Render difficult Hebrew combinations and native-pixel small-text samples.

Cantillation and repeated mark combinations are synthetic stress strings,
not claims about correct Hebrew spelling or accentuation.
"""

from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from hebrew_raster import render_text


OUT = Path("out")
FONT = OUT / "GoogleSans-HebrewGrade-Prototype.ttf"
AXES = TTFont(FONT)["fvar"].axes
LABEL = str(FONT)  # Reuse the built font for labels; no system font required.
CASES = [
    ("Letters and final forms", "אבגדהוזחטיךכלםמןנסעףפץצקרשת"),
    ("Tight pairs / repeated strokes", "חח הה חה ההה ממ םם שש עע צץ פף"),
    ("Vowels in running text", "שָׁלוֹם עוֹלָם, אֵיךְ אַתָּה מַרְגִּישׁ?"),
    ("Dots, vowels and final letters", "שׁ שׂ שּׁ שּׂ בּ כּ פּ ךְ ךָ ףּ לֹ לֹּ"),
    ("Stacked vowels / mark combinations", "בֲ בֱ בֳ חֲ חֱ חֳ אֲ אֱ אֳ וּ וֹ יִ"),
    ("Cantillation stress: synthetic", "בְּ֑ בָּ֖ ב֣ שָׁ֥ שִׂ֔ לֹ֗ מִֽ ךָ֙ תּ֛"),
    ("Hebrew punctuation", "תשפ״ז • כיתה ז׳ • א־ב • א–ב • (שלום)"),
    ("Mixed scripts / numerals", "חיפוש English 123: שיעור ב־08:30"),
    ("Longer text / spacing", "מחר נלמד מתמטיקה, עברית ואנגלית."),
]
SETTINGS = [(400, 0), (400, 100), (400, 200), (700, 0), (700, 100), (700, 200)]


def font_at(pixels, weight, grade, optical_size=18):
    font = ImageFont.truetype(str(FONT), pixels)
    values = {"wght": weight, "GRAD": grade, "opsz": optical_size}
    font.set_variation_by_axes([values[a.axisTag] for a in AXES])
    return font


def main():
    # Large specimens, with one independent panel per weight/grade setting.
    width, height = 2300, 2450
    image = Image.new("RGB", (width * 3, height * 2), "#fafafa")
    draw = ImageDraw.Draw(image)
    heading = ImageFont.truetype(LABEL, 60)
    label = ImageFont.truetype(LABEL, 34)
    for index, (weight, grade) in enumerate(SETTINGS):
        x, y = (index % 3) * width, (index // 3) * height
        draw.text(
            (x + 70, y + 45),
            f"wght {weight} | GRAD {grade} | opsz 18",
            font=heading,
            fill="#111111",
        )
        for row, (title, text) in enumerate(CASES):
            top = y + 170 + row * 245
            draw.text((x + 70, top), title, font=label, fill="#555555")
            font = font_at(108, weight, grade)
            assert draw.textlength(text, font=font, direction="rtl") <= width - 140, (
                title
            )
            draw.text(
                (x + width - 70, top + 65),
                text,
                anchor="rt",
                direction="rtl",
                font=font,
                fill="#111111",
            )
    image.save(OUT / "hebrew-stress-comparison.png")

    # These are genuinely small rasterizations, not enlarged text. Pixel sizes
    # are not Android sp: device density, font scaling, and renderer differ.
    image = Image.new("RGB", (1700, 2000), "#fafafa")
    draw = ImageDraw.Draw(image)
    heading = ImageFont.truetype(LABEL, 22)
    label = ImageFont.truetype(LABEL, 16)
    draw.text(
        (25, 15),
        "Native-pixel samples: view at 100%. Desktop rendering, NOT Android sp.",
        font=heading,
        fill="#111111",
    )
    for index, (weight, grade) in enumerate(SETTINGS):
        x, y = (index % 2) * 850, 65 + (index // 2) * 640
        draw.text(
            (x + 25, y),
            f"wght {weight} | GRAD {grade} | opsz 17",
            font=heading,
            fill="#111111",
        )
        for row, pixels in enumerate((12, 14, 16, 20)):
            top = y + 50 + row * 125
            draw.text((x + 25, top), f"{pixels}px", font=label, fill="#555555")
            font = font_at(pixels, weight, grade, optical_size=17)
            for line, text in enumerate((CASES[2][1], CASES[3][1], CASES[7][1])):
                if line < 2:
                    # Preserve fractional glyph origins for the Hebrew rows.
                    # Keep RAQM below for the mixed-script row's bidi handling.
                    tile = render_text(
                        FONT,
                        text,
                        pixels,
                        {"wght": weight, "GRAD": grade, "opsz": 17},
                        canvas=(450, 40),
                        baseline=(0, pixels + 5),
                    )
                    image.paste(tile, (x + 360, top + line * 40))
                    continue
                draw.text(
                    (x + 810, top + line * 40),
                    text,
                    anchor="rt",
                    direction="rtl",
                    font=font,
                    fill="#111111",
                )
    image.save(OUT / "hebrew-small-text-native-pixels.png")
    print("Rendered out/hebrew-stress-comparison.png: 6900 x 4900")
    print("Rendered out/hebrew-small-text-native-pixels.png: 1700 x 2000")


if __name__ == "__main__":
    main()
