"""Build reproducible upstream/fork fonts and run Hebrew checks from a clean clone.

No network or saved experimental fonts are needed. The pinned upstream commit
must exist in the local Git history; use a full clone rather than a shallow one.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time

import ots

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"


def run(arguments, *, cwd=ROOT, log=None):
    print("+ " + " ".join(map(str, arguments)), flush=True)
    if log:
        with log.open("w") as stream:
            subprocess.run(
                arguments, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, check=True
            )
    else:
        subprocess.run(arguments, cwd=cwd, check=True)


def build(source_root, designspace, target, log):
    run(
        [
            sys.executable,
            "-m",
            "fontmake",
            "-m",
            str(source_root / "sources" / designspace),
            "-o",
            "variable",
            "--output-path",
            str(target),
        ],
        cwd=source_root,
        log=log,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--specimens", action="store_true", help="Also render PNG specimens"
    )
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    pin = (ROOT / "qa/hebrew-baseline.txt").read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", pin):
        parser.error("qa/hebrew-baseline.txt must contain a full commit SHA")
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{pin}:sources"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        parser.error(
            f"Upstream baseline {pin} is missing; fetch full Git history first"
        )

    started = time.monotonic()
    run([sys.executable, "scripts/prototype-hebrew-grade.py", "--check"])
    run([sys.executable, "-m", "unittest", "qa.test_shaping_fixture_scope"])
    # A new temporary tree on every run prevents a fork build from silently
    # being reused as the original baseline. Only archive tracked source files.
    with tempfile.TemporaryDirectory(prefix="hebrew-baseline-", dir=OUT) as directory:
        temporary = Path(directory)
        archive = temporary / "sources.tar"
        with archive.open("wb") as stream:
            subprocess.run(
                ["git", "archive", pin, "sources"], cwd=ROOT, stdout=stream, check=True
            )
        with tarfile.open(archive) as tar:
            tar.extractall(temporary, filter="data")
        for italic in (False, True):
            style = "Italic-" if italic else ""
            designspace = (
                "GoogleSans-Italic.designspace" if italic else "GoogleSans.designspace"
            )
            baseline = OUT / f"GoogleSans-{style}Baseline.ttf"
            fork = OUT / f"GoogleSans-{style}HebrewGrade-Prototype.ttf"
            build(
                temporary,
                designspace,
                baseline,
                OUT / f"hebrew-{style}baseline-build.log",
            )
            build(ROOT, designspace, fork, OUT / f"hebrew-{style}fork-build.log")
            run(
                [
                    sys.executable,
                    "scripts/check-finalkaf-rendering.py",
                    "--font",
                    str(fork),
                    "--baseline",
                    str(baseline),
                ]
            )
            sanitized = OUT / f"GoogleSans-{style}sanitizer-check.ttf"
            result = ots.sanitize(
                str(fork), str(sanitized), check=True, capture_output=True
            )
            print(result.stdout.decode(), end="")
            sanitized.unlink()

    run([sys.executable, "scripts/check-hebrew-joins.py"])
    run(
        [
            sys.executable,
            "scripts/check-hebrew-grade.py",
            *([] if args.specimens else ["--no-render"]),
        ]
    )
    run([sys.executable, "scripts/check-hebrew-spacing.py"])
    if args.specimens:
        run([sys.executable, "scripts/render-hebrew-stress.py"])
    fonts = [
        OUT / "GoogleSans-Baseline.ttf",
        OUT / "GoogleSans-Italic-Baseline.ttf",
        OUT / "GoogleSans-HebrewGrade-Prototype.ttf",
        OUT / "GoogleSans-Italic-HebrewGrade-Prototype.ttf",
    ]
    report = {
        "upstream_commit": pin,
        "checked_styles": ["upright", "italic"],
        "elapsed_seconds": round(time.monotonic() - started, 1),
        "fonts_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in fonts
        },
    }
    (OUT / "hebrew-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: Hebrew validation completed; report: out/hebrew-validation.json")


if __name__ == "__main__":
    main()
