# Google Sans Hebrew fixes

An experimental fork of [Google Sans](https://github.com/googlefonts/googlesans)
focused on Hebrew rendering, spacing, mark placement, and variable-font grade
support. This is an independent project, not an official Google release.

The work began with missing Hebrew `GRAD` variations. Review of the resulting
font also exposed issues present in the original Hebrew design. This fork tracks
both upstream issues and defects introduced while extending the font.

## Implemented changes

- **Positive Hebrew grade.** Added weight-derived grade variations to 143 Hebrew
  glyphs in each upright optical-size grade master, including letters, marks,
  and composites where the weight masters provide usable differences. Advance
  widths are preserved. Some cantillation outlines are identical across weights
  and therefore still have no grade change.
- **Ayin join.** Removed the notch introduced at high weight and grade by
  extending the diagonal into the lower curve. Its existing edge direction is
  preserved rather than straightening the original design's slight bend.
- **Het join.** Removed the top-left overhang introduced at high weight and grade.
- **Final kaf with vowels.** Removed four substitutions that combined final kaf
  and sheva/qamats, with and without dagesh. Those combined glyphs rendered too
  low in small-size FreeType tests. Existing mark positioning now places the
  vowels beside the base glyph instead. This fixes the original visible drop
  and the additional drop triggered by positive grade, without raising outlines
  or changing advance widths.

## Planned fixes and review

- [ ] **Yod spacing review.** The original spacing is currently retained,
  with no centering shift. Earlier centering changes were withdrawn after reviewing native
  small text. Do not treat those experimental changes as an implemented fix.
- [ ] **Niqqud clearance.** Identify and correct unwanted contacts between vowel
  marks and letters at small sizes, especially at high weight and grade. Test
  mark placement and thickness together rather than shifting every mark down.
- [ ] **Cantillation grade.** Design thickness changes for marks whose identical
  Regular/Bold outlines give the current generator no variation to work with.
- [ ] **Android validation.** Check actual UI sizes, device densities, font
  scaling, and light/dark backgrounds. Desktop specimens are not Android tests.
- [ ] **Broader coverage.** Review intermediate axis settings, crowded mark
  sequences, mixed Hebrew/Latin text, clipping, and line spacing.
- [ ] **Negative grade and italics.** Extend and validate the fixes as appropriate.
  Hebrew grade changes currently cover positive grade in upright sources only.
  The shared final-kaf shaping change is checked in both styles; italic grade
  design and broader italic visual review remain out of scope.

## Status and validation

The font is a prototype, not a finished release. Current checks cover source
join geometry, shaped advances, mark positioning, small-size final-kaf rendering,
and OpenType sanitization. Visual specimens include the full Hebrew alphabet,
niqqud, synthetic cantillation combinations, punctuation, and mixed scripts.

Preserving advance widths does not guarantee adequate visual spacing. Grade-zero
outlines are unchanged, but the final-kaf correction intentionally changes
shaping. Experimental yod kerning changes have been removed, restoring original
pair spacing and advances.

See [the development notes](HEBREW-GRADE-PROTOTYPE.md) for the generation method,
checks, local comparison files, and known limitations. The grade generator
includes the ayin and het corrections so regenerating the masters retains them.

## Sources and builds

Sources are UFO masters and designspace files under `sources/`. Existing axes:

| Axis | Range | Default |
| --- | --- | --- |
| `wght` | 400–700 | 400 |
| `opsz` | 17–18 | 18 |
| `GRAD` | −50–200 | 0 |

Grade is available in variable fonts. The two optical-size endpoints correspond
to Google Sans Text and Google Sans.

For reproducible builds and Hebrew regression checks, install `uv` and use
Python 3.12 with a full Git clone:

```bash
make check-hebrew
# Also generate the alphabet, stress, and native-pixel specimens:
make hebrew-specimens
```

These commands build both styles and recreate upstream reference fonts from the
commit pinned in `qa/hebrew-baseline.txt`. They need no saved experimental font
files or machine-specific system fonts. See the development notes for manual
Python commands, output paths, and exactly what is checked.

The upstream `Makefile` provides the broader build pipeline through `make build`.
Some upstream build
documentation describes older targets and paths. Upstream usage and maintenance
documentation remain in [USAGE.md](USAGE.md) and [docs/MAINTAINER.md](docs/MAINTAINER.md).

## GitHub Actions

Build, test, and comparison workflows use standard `ubuntu-24.04` GitHub-hosted
runners rather than Google's private runners. The Hebrew regression job runs
the same clean-clone validation and uploads fonts, specimens, logs, and reports.
Fork owners may need to enable Actions in their repository settings. Hosted
runtime and memory limits still apply; local validation does not prove a hosted
workflow will pass before its first run.

## AI usage

This fork was developed with AI assistance for font inspection, modification
scripts, outline corrections, tests, and documentation. Changes were iteratively
reviewed by the maintainer using rendered specimens. AI-generated changes and
passing tests do not replace type-design expertise or on-device visual testing.

## License and attribution

The font remains under the [SIL Open Font License 1.1](OFL.txt), without Reserved
Font Names. Preserve the upstream copyright notices and license when distributing
modified fonts. See [TRADEMARKS.txt](TRADEMARKS.txt) for naming guidance. Internal
font names have not yet been changed; this fork does not imply endorsement by
Google.
