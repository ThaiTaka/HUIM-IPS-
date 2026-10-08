"""Find every character used in the figures and the deck that Times New Roman
cannot actually render.

This exists because a missing glyph does not fail loudly: matplotlib draws a
"tofu" box and PowerPoint silently substitutes another font. The only reliable
check is to open the font file and ask which code points it maps.

Run:  python src/check_glyphs.py          # report
      python src/check_glyphs.py --all    # also scan the Word report sources
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import PROJECT_ROOT, dump_json, get_logger, RESULTS

LOG = get_logger("glyphs", "glyphs.log")

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/times.ttf"),
    Path("C:/Windows/Fonts/Times New Roman.ttf"),
    Path("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf"),
]

# Replacements for characters Times New Roman lacks. Chosen to keep the meaning
# rather than to look clever: a double arrow becomes a single arrow, set
# membership is spelled out, and so on.
SAFE_REPLACEMENTS = {
    "\u27f9": "=>",      # LONG RIGHTWARDS DOUBLE ARROW
    "\u21d2": "=>",      # RIGHTWARDS DOUBLE ARROW
    "\u27f6": "\u2192",  # LONG RIGHTWARDS ARROW -> RIGHTWARDS ARROW
    "\u27fa": "<=>",     # LONG LEFT RIGHT DOUBLE ARROW
    "\u21d4": "<=>",     # LEFT RIGHT DOUBLE ARROW
    "\u2211": "T\u1ed5ng",   # N-ARY SUMMATION
    "\u220f": "T\u00edch",   # N-ARY PRODUCT
    "\u2208": " thu\u1ed9c ",  # ELEMENT OF
    "\u2209": " kh\u00f4ng thu\u1ed9c ",
    "\u2286": " l\u00e0 t\u1eadp con c\u1ee7a ",  # SUBSET OF OR EQUAL TO
    "\u2282": " l\u00e0 t\u1eadp con c\u1ee7a ",
    "\u2205": "{ }",     # EMPTY SET
    "\u227a": "<",       # PRECEDES
    "\u227b": ">",       # SUCCEEDS
    "\u2229": " giao ",  # INTERSECTION
    "\u222a": " h\u1ee3p ",  # UNION
    "\u2264": "<=",      # LESS-THAN OR EQUAL TO (TNR has it, kept for safety)
    "\u2265": ">=",
    "\u2260": "!=",
    "\u00d7": "x",
    "\u00b7": ".",
    "\u2248": "~",
    "\u03c1": "rho",
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u2261": "=",       # IDENTICAL TO
}


def load_cmap() -> tuple[set[int], Path]:
    from fontTools.ttLib import TTFont
    for p in FONT_CANDIDATES:
        if p.exists():
            f = TTFont(str(p), fontNumber=0, lazy=True)
            cps: set[int] = set()
            for table in f["cmap"].tables:
                cps |= set(table.cmap.keys())
            f.close()
            return cps, p
    raise FileNotFoundError(
        "Times New Roman not found in " + ", ".join(str(p) for p in FONT_CANDIDATES))


def string_literals(path: Path) -> list[tuple[int, str]]:
    """Every string literal in a Python source file, with its line number."""
    src = path.read_text(encoding="utf-8")
    out = []
    pat = re.compile(r'"""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\'|'
                     r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
    for m in pat.finditer(src):
        line = src[:m.start()].count("\n") + 1
        out.append((line, m.group(0)))
    return out


def scan(paths: list[Path], cps: set[int]) -> list[dict]:
    bad = []
    for p in paths:
        if not p.exists():
            continue
        for line, lit in string_literals(p):
            for ch in set(lit):
                o = ord(ch)
                if o < 32 or ch in '"\'\\':
                    continue
                if o not in cps:
                    bad.append({
                        "file": str(p.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                        "line": line,
                        "char": ch,
                        "codepoint": f"U+{o:04X}",
                        "name": _uname(ch),
                        "suggested_replacement": SAFE_REPLACEMENTS.get(ch),
                        "context": lit[:90].replace("\n", " "),
                    })
    return bad


def _uname(ch: str) -> str:
    import unicodedata
    try:
        return unicodedata.name(ch)
    except ValueError:
        return "?"


def main() -> None:
    cps, font_path = load_cmap()
    LOG.info("Times New Roman at %s maps %d code points", font_path, len(cps))

    targets = [PROJECT_ROOT / "src" / "make_diagrams.py",
               PROJECT_ROOT / "src" / "make_slides.py",
               PROJECT_ROOT / "src" / "plots.py"]
    if "--all" in sys.argv:
        targets += sorted((PROJECT_ROOT / "src").glob("report_parts*.py"))
        targets.append(PROJECT_ROOT / "src" / "make_report.py")

    bad = scan(targets, cps)
    # de-duplicate for the console summary
    uniq: dict[str, dict] = {}
    for b in bad:
        uniq.setdefault(b["codepoint"], {**b, "count": 0})
        uniq[b["codepoint"]]["count"] += 1

    dump_json({"font": str(font_path), "n_codepoints_in_font": len(cps),
               "files_scanned": [str(t.relative_to(PROJECT_ROOT)).replace("\\", "/")
                                 for t in targets],
               "n_occurrences": len(bad),
               "distinct_missing": list(uniq.values()),
               "all_occurrences": bad},
              RESULTS / "glyph_check.json")

    if not bad:
        print(f"OK - every character in {len(targets)} files is present in "
              f"Times New Roman")
        return
    print(f"MISSING GLYPHS ({len(bad)} occurrences, "
          f"{len(uniq)} distinct) in Times New Roman:\n")
    for cp, b in sorted(uniq.items()):
        rep = b["suggested_replacement"]
        print(f"  {b['char']}  {cp}  {b['name'][:40]:42s} x{b['count']:<4d} "
              f"-> {rep!r}" if rep else
              f"  {b['char']}  {cp}  {b['name'][:40]:42s} x{b['count']:<4d} "
              f"-> NO REPLACEMENT DEFINED")
    print("\nOccurrences:")
    for b in bad:
        print(f"  {b['file']}:{b['line']}  {b['codepoint']}  {b['context']}")
    sys.exit(1)


if __name__ == "__main__":
    main()
