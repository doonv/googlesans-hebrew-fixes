# Hebrew font development and validation

## What the generator changes

`scripts/prototype-hebrew-grade.py` processes 143 Hebrew glyphs in each of the
two upright `GRAD200` UFO masters. It derives positive grade from the existing
Regular-to-Bold outline differences, using 55% of that difference at grade 200.
The heavier design is horizontally translated into the original advance width.
Anchors and component translations are adjusted too. Outline topology, advance
widths, and kerning are preserved.

The generator also corrects the ayin notch and het overhang found during review.
It always reads the unchanged grade-zero and Bold masters, so rerunning it does
not compound the previous result. Integer coordinates follow the upstream UFO
normalization conventions.

This is a weight-derived approximation, not a pure stroke expansion or a
professionally corrected grade. Marks with identical Regular/Bold outlines,
including much of the cantillation, receive no new variation. Negative Hebrew
grade and italic grade have not been designed.

## Reproduce from a fresh clone

Use Python 3.12, Git, `uv`, and `make`. A full Git history is required; the
upstream reference is pinned in `qa/hebrew-baseline.txt`.

```bash
make check-hebrew
```

This installs the declared dependencies into a uv-managed environment, then:

1. Extracts the pinned upstream `sources/` into a new temporary directory.
2. Builds upstream and fork variable fonts, both upright and italic.
3. Checks final-kaf shaping, actual rendered body alignment, and mark placement.
4. Runs OpenType Sanitizer on both fork fonts.
5. Checks upright join geometry, grade/layout behavior, and original pair spacing.
6. Writes `out/hebrew-validation.json` with the upstream SHA and font hashes.

It does not change tracked sources or use old experimental TTFs. It rebuilds
the references on each run rather than trusting a possibly stale local baseline.
If the pinned commit is absent in a shallow clone, fetch the missing history
first. No font downloads or Google-specific build machines are required.

To generate the visual specimens as well:

```bash
make hebrew-specimens
```

Alternatively, install `requirements-dev.txt` in a Python 3.12 environment and
run `python scripts/check-hebrew.py --specimens`. The direct fontmake outputs
used by these checks are development builds, not the complete release pipeline.
The upstream `make build` pipeline remains available and builds both styles.

## Baselines and intentional shaping changes

The baseline is built from commit `10c1a0fd02fa1f6d0479480668546e81ab84b3b3`,
not from this fork's already-modified working tree. Update the pin deliberately
when rebasing, after reviewing upstream changes and their effect on tests.

`sources/family.fea` removes four final-kaf/sheva/qamats substitutions, including
dagesh forms. Existing mark positioning handles the separate base and vowel.
Grade-zero outlines stay unchanged, but glyph selection intentionally changes.

General grade-zero comparisons remove only these four substitutions from the
upstream baseline in memory. The final-kaf test separately restores the original
rules in the fork font in memory to compare positioned outlines at every grade.
This preserves an upstream-derived pre-fix reference without storing historical
experimental font binaries. Advances must match, and positioned outline points
may differ by at most 2/1000 em due to positioning/outline rounding.

The raster test compares the actual marked letter's rendered pixels above the
baseline with the corresponding unmarked letter. It therefore catches a visible
drop, rather than merely comparing the same glyph's bitmap metrics twice.
Both upright and italic shaping/rendering are checked because the feature file
is shared. Passing these checks is not a visual endorsement of italic design.

## Release-pipeline shaping fixtures

`qa/shaping_input/ccmp_hebr_finalkaf.toml` adds final-kaf/vowel and cantillation
cases to the existing QA suite. Its committed JSON expectations cover both
variable styles and all twelve static instances. The existing Hebrew shaping
fixtures are retained rather than regenerated indiscriminately.

After `make build static`, check those release outputs with:

```bash
uv run --python 3.12 --with-requirements requirements-dev.txt python scripts/check-hebrew-fixtures.py
uv run --python 3.12 --with-requirements requirements-dev.txt python scripts/check-hebrew-fixtures.py --font-dir fonts/static
```

GitHub Actions runs these fixture checks as well as the independent source-based
Hebrew regression job. Changes to shaping should update only the affected
expectations after reviewing the actual glyph selections and offsets.

Older fixtures that contain only variable-font expectations explicitly skip
static builds; they do not pretend to cover them. The final-kaf fixture includes
all fourteen release-pipeline outputs. Empty/mixed fixtures and missing variable
font entries still fail. Unit tests guard this distinction, and the standalone
Hebrew fixture checker requires at least one applicable fixture for every font.

## Current spacing and specimen rendering

Original yod spacing is retained. The experimental yod–shin/gimel–yod kerning
changes were withdrawn after native-size review; no maintenance script deletes
or adds kerning. `check-hebrew-spacing.py` guards upstream-compatible base-letter
positions and advances, including marked forms and intermediate optical size.
Mark offsets may change with grade and are tested separately.

Hebrew-only native-pixel samples use HarfBuzz and FreeType with fractional glyph
origins. The mixed-script row and large specimens use Pillow/RAQM for bidi
handling. Different rendering pipelines may give different pixel output. View
native samples at 100%, not scaled to fit a window. Pixel sizes are not Android sp.
Specimen labels reuse the built font, so no machine-specific system font is needed.

Outputs are ignored build artifacts under `out/`:

- `GoogleSans-HebrewGrade-Prototype.ttf` and its italic counterpart.
- `GoogleSans-Baseline.ttf` and its italic counterpart.
- `hebrew-validation.json`, `hebrew-grade-checks.json`, and build logs.
- `hebrew-grade-comparison.png`, `hebrew-stress-comparison.png`, and
  `hebrew-small-text-native-pixels.png` when specimens are requested.

After validation, higher-resolution alphabet comparisons can be generated with
`python scripts/check-hebrew-grade.py --scale 3`. Original ayin close-ups remain
available through `scripts/render-original-ayin.py`.

## Limits and distribution

Niqqud collisions, cantillation grade, and Android validation remain follow-up
work. Desktop geometry, shaping, and sanitizer checks do not certify type-design
quality or cover every possible mark sequence. Preserve `OFL.txt` and upstream
copyright notices with distributed fonts; see `TRADEMARKS.txt` for naming guidance.
This fork is not endorsed by Google.
