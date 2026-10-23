"""Generate an experimental positive Hebrew grade from existing weight masters.

Run from the repository root. Only the two upright GRAD200 UFOs are edited.
Advance widths, kerning, point topology, and component references are preserved.
This is a weight-derived approximation, not an optically corrected type design.
"""

import argparse
from copy import deepcopy
from pathlib import Path

from ufoLib2 import Font
from internal.normalize import clean_number


def signature(glyph):
    return (
        [[p.type for p in contour.points] for contour in glyph.contours],
        [c.baseGlyph for c in glyph.components],
        [a.name for a in glyph.anchors],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strength", type=float, default=0.55)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated glyphs without writing sources",
    )
    args = parser.parse_args()
    if not 0 < args.strength <= 1:
        parser.error("strength must be greater than zero and at most one")

    for size in (17, 18):
        prefix = Path("sources") / f"GoogleSans-opsz{size}"
        regular = Font.open(f"{prefix}-wght380-GRAD0.ufo")
        bold = Font.open(f"{prefix}-wght734-GRAD0.ufo")
        target = Font.open(f"{prefix}-wght380-GRAD200.ufo")
        names = sorted(n for n in regular.keys() if n.endswith("-hb") or "-hb." in n)
        previous = (
            {name: deepcopy(target[name]) for name in names} if args.check else None
        )

        def mix(a, b):
            return clean_number(round(a + args.strength * (b - a), 3))

        def shift(name):
            # Center the heavier design in the original advance width. Zero-width
            # marks stay zero-width and retain their original coordinate origin.
            return (regular[name].width - bold[name].width) / 2

        # Validate everything before editing this optical-size master.
        for name in names:
            assert signature(regular[name]) == signature(bold[name]), name
            assert signature(regular[name]) == signature(target[name]), name

        for name in names:
            r, b, t = regular[name], bold[name], target[name]
            t.width = r.width
            t.height = r.height
            for rc, bc, tc in zip(r.contours, b.contours, t.contours):
                for rp, bp, tp in zip(rc.points, bc.points, tc.points):
                    tp.x = mix(rp.x, bp.x + shift(name))
                    tp.y = mix(rp.y, bp.y)
            for ra, ba, ta in zip(r.anchors, b.anchors, t.anchors):
                ta.x = mix(ra.x, ba.x + shift(name))
                ta.y = mix(ra.y, ba.y)
            for rc, bc, tc in zip(r.components, b.components, t.components):
                # A component's own grade already includes its centering shift.
                # Remove that shift before placing it in the parent coordinate
                # system, then apply the parent's centering shift.
                xx, xy, yx, yy, dx, dy = bc.transformation
                # Shared Latin punctuation is left on its existing grade design.
                child_shift = shift(bc.baseGlyph) if bc.baseGlyph in names else 0
                adjusted = (
                    xx,
                    xy,
                    yx,
                    yy,
                    dx + shift(name) - xx * child_shift,
                    dy - xy * child_shift,
                )
                tc.transformation = tuple(
                    mix(a, b) for a, b in zip(rc.transformation, adjusted)
                )
            assert t.width == r.width
            assert signature(t) == signature(r)
        # Ayin's bottom-right diagonal endpoint is an internal join, not a
        # visible edge. Weight-derived vertical movement lifts it out of the
        # bowl at Bold + high grade, leaving a small white notch. Keep its
        # original height so the contours retain a generous overlap.
        ra, ba, ta = (f["ayin-hb"] for f in (regular, bold, target))
        rj, bj, tj = (g.contours[1].points[1] for g in (ra, ba, ta))
        rn, bn, tn = (g.contours[1].points[2] for g in (ra, ba, ta))
        join_x, join_y = bj.x + tj.x - rj.x, bj.y + tj.y - rj.y
        next_x, next_y = bn.x + tn.x - rn.x, bn.y + tn.y - rn.y
        drop = rj.y - tj.y
        # Extend the existing sloped edge rather than pivoting it when lowering
        # the endpoint. Pivoting would introduce a new visible kink above it.
        tj.x = clean_number(
            round(tj.x + drop * (join_x - next_x) / (join_y - next_y), 3)
        )
        tj.y = rj.y

        # Het's top and left stem are separate overlapping contours. At the
        # heavy corner the top's left edge must remain inside the stem. Keep
        # two units of inset, while preserving the existing point topology.
        rh, bh, th = (f["het-hb"] for f in (regular, bold, target))
        stem = (
            bh.contours[1].points[3].x
            + th.contours[1].points[3].x
            - rh.contours[1].points[3].x
        )
        minimum = rh.contours[0].points[6].x + stem + 2 - bh.contours[0].points[6].x
        for index in (6, 7):
            th.contours[0].points[index].x = max(
                th.contours[0].points[index].x, minimum
            )
        if args.check:
            differences = [name for name in names if target[name] != previous[name]]
            assert not differences, (
                f"Generated grade differs from checked-in sources: {differences}"
            )
        else:
            target.save()
        print(
            f"opsz={size}: {'verified' if args.check else 'updated'} {len(names)} Hebrew glyphs, strength={args.strength}"
        )


if __name__ == "__main__":
    main()
