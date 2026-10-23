"""Normalize the old baseline's final-kaf substitutions for regression checks."""

import io
from copy import deepcopy

from fontTools.ttLib import TTFont

FINAL_KAF_LIGATURES = {"uni05DA05B0", "uni05DA05B8", "uniFB3A05B0", "uniFB3A05B8"}


def without_finalkaf_vowel_ligatures(data):
    font = TTFont(io.BytesIO(data))
    for lookup in font["GSUB"].table.LookupList.Lookup:
        for table in lookup.SubTable:
            for base, ligatures in getattr(table, "ligatures", {}).items():
                table.ligatures[base] = [
                    lig for lig in ligatures if lig.LigGlyph not in FINAL_KAF_LIGATURES
                ]
    output = io.BytesIO()
    font.save(output)
    return output.getvalue()


def with_original_finalkaf_substitutions(data, baseline):
    """Restore upstream's four rules in memory, retaining the current outlines.

    This reconstructs the pre-fix behavior at every grade without depending on
    an untracked experimental font. The rules and lookup flags come from the
    pinned upstream baseline, not handwritten copies of the old behavior.
    """
    font = TTFont(io.BytesIO(data))
    original = TTFont(io.BytesIO(baseline))
    candidates = []
    for lookup in original["GSUB"].table.LookupList.Lookup:
        for table in lookup.SubTable:
            rules = [
                (base, lig)
                for base, ligs in getattr(table, "ligatures", {}).items()
                for lig in ligs
                if lig.LigGlyph in FINAL_KAF_LIGATURES
            ]
            if rules:
                candidates.append((lookup, table, rules))
    assert len(candidates) == 1, "Expected one upstream diacritic-replacement lookup"
    old_lookup, old_table, rules = candidates[0]
    assert len(rules) == 4
    # Identify the matching lookup by its unaffected alef+patah substitution.
    matches = [
        (lookup, table)
        for lookup in font["GSUB"].table.LookupList.Lookup
        for table in lookup.SubTable
        if any(
            lig.LigGlyph == "uniFB2E"
            for ligs in getattr(table, "ligatures", {}).values()
            for lig in ligs
        )
    ]
    assert len(matches) == 1
    lookup, table = matches[0]
    assert lookup.LookupFlag == old_lookup.LookupFlag
    for base, ligature in rules:
        existing = table.ligatures.setdefault(base, [])
        assert not any(lig.LigGlyph == ligature.LigGlyph for lig in existing)
        existing.append(deepcopy(ligature))
    output = io.BytesIO()
    font.save(output)
    return output.getvalue()
