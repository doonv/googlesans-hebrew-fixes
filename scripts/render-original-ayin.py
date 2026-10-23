"""Render unmodified ayin at weights 400–700, optical size 18, grade zero."""

from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont


out = Path("out")
path = out / "GoogleSans-Baseline.ttf"
axes = TTFont(path)["fvar"].axes
label = ImageFont.truetype(str(path), 48)
grid = Image.new("RGB", (3600, 3600), "#fafafa")
for index, weight in enumerate((400, 500, 600, 700)):
    panel = Image.new("RGB", (1800, 1800), "#fafafa")
    draw = ImageDraw.Draw(panel)
    draw.text(
        (70, 50),
        f"Original | wght {weight} | GRAD 0 | opsz 18",
        font=label,
        fill="#333333",
    )
    font = ImageFont.truetype(str(path), 1800)
    values = {"wght": weight, "opsz": 18, "GRAD": 0}
    font.set_variation_by_axes([values[a.axisTag] for a in axes])
    draw.text((1500, 250), "ע", anchor="rt", direction="rtl", font=font, fill="#111111")
    panel.save(out / f"original-ayin-wght{weight}-grad0.png")
    grid.paste(panel, ((index % 2) * 1800, (index // 2) * 1800))
grid.save(out / "original-ayin-weights-grad0.png")
print("Rendered out/original-ayin-weights-grad0.png: 3600 x 3600")
print("Also saved four individual 1800 x 1800 close-ups.")
