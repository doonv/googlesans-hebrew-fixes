"""Check the reported ayin notch and het overhang in the source designspace."""

from copy import deepcopy

import pathops
from ufoLib2 import Font


def interpolate(r, b, t, weight, grade):
    glyph = deepcopy(r)
    for rc, bc, tc, contour in zip(r.contours, b.contours, t.contours, glyph.contours):
        for rp, bp, tp, point in zip(rc.points, bc.points, tc.points, contour.points):
            point.x = rp.x + weight * (bp.x - rp.x) + grade * (tp.x - rp.x)
            point.y = rp.y + weight * (bp.y - rp.y) + grade * (tp.y - rp.y)
    return glyph


def main():
    failures = []
    cases = 0
    for size in (17, 18):
        r, b, t = [
            Font.open(f"sources/GoogleSans-opsz{size}-wght{w}-GRAD{g}.ufo")
            for w, g in ((380, 0), (734, 0), (380, 200))
        ]
        for weight in (0, 0.25, 0.5, 0.75, 1):
            for grade in (0, 0.25, 0.5, 0.75, 1):
                a = interpolate(r["ayin-hb"], b["ayin-hb"], t["ayin-hb"], weight, grade)
                bowl = pathops.Path()
                a.contours[0].draw(bowl.getPen())
                join = a.contours[1].points[1]
                if not bowl.contains((join.x, join.y)):
                    failures.append(
                        f"ayin notch: opsz={size} weight={weight} grade={grade}"
                    )
                h = interpolate(r["het-hb"], b["het-hb"], t["het-hb"], weight, grade)
                if h.contours[0].points[6].x < h.contours[1].points[3].x:
                    failures.append(
                        f"het overhang: opsz={size} weight={weight} grade={grade}"
                    )
                cases += 2
    assert not failures, "\n".join(failures)
    print(
        f"PASS: {cases} join checks across both optical sizes and a 5x5 weight/grade grid"
    )


if __name__ == "__main__":
    main()
