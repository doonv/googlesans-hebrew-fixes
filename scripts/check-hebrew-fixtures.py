"""Check committed Hebrew shaping fixtures against release-pipeline fonts."""

import argparse
import json
from pathlib import Path
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from qa.update_shaping_test_data import (
    ComparisonMode,
    Direction,
    shape_texts,
    has_only_variable_expectations,
)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--font-dir", type=Path, default=Path("fonts/variable"))
args = parser.parse_args()
fonts = sorted(args.font_dir.glob("*.ttf"))
assert fonts, f"No fonts in {args.font_dir}; run make build first"
cases = 0
skipped = 0
failures = []
for path in fonts:
    font = TTFont(path)
    face = hb.Face(path.read_bytes())
    checked_for_font = 0
    for fixture in sorted((ROOT / "qa/shaping").glob("*hebr*.json")):
        data = json.loads(fixture.read_text())
        inputs = data["input"]
        expected = data["output"].get(path.name)
        if expected is None:
            if "fvar" not in font and has_only_variable_expectations(data["output"]):
                skipped += 1
                continue
            failures.append(f"{fixture.name}: missing {path.name}")
            continue
        actual = shape_texts(
            font,
            face,
            inputs["text"],
            inputs.get("script"),
            inputs.get("language"),
            Direction(inputs.get("direction", "ltr")),
            inputs.get("features", {}),
            ComparisonMode(inputs.get("comparison_mode", "full")),
        )
        if actual != expected:
            failures.append(f"{fixture.name}: shaping changed in {path.name}")
        cases += 1
        checked_for_font += 1
    assert checked_for_font, f"No applicable Hebrew fixtures for {path.name}"
assert not failures, "\n".join(failures)
print(
    f"PASS: {cases} Hebrew fixture/font comparisons; {skipped} variable-only fixtures skipped"
)
