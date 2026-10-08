"""PHASE L (entry point) - assemble the Word report from all chapter modules.

Chapters live in:
    make_report.py    cover, table of contents, ch1-ch3
    report_parts2.py  ch4-ch8
    report_parts3.py  ch9-ch11
    report_parts4.py  ch12-ch14, ch16, references
    report_parts5.py  ch15, ch17-ch18, appendix cheat sheet

Order in the document follows the brief: ... 14 Ablation, 15 Reverse-thinking,
16 Limitations, 17 Conclusion, 18 Future work, References, Appendix.

Run: python src/build_report.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_report as mr
import report_parts2 as p2
import report_parts3 as p3
import report_parts4 as p4
import report_parts5 as p5
from report_builder import Doc
from utils import REPORT, dump_json, get_logger

LOG = get_logger("buildreport", "report.log")

OUT = REPORT / "HUIM_IPS_UJIIndoorLoc_Important_Knowledge.docx"


def main() -> None:
    C = mr.Ctx()
    D = Doc()

    mr.cover(D, C)
    mr.ch1(D, C)
    mr.ch2(D, C)
    mr.ch3(D, C)
    p2.ch4(D, C)
    p2.ch5(D, C)
    p2.ch6(D, C)
    p2.ch6b(D, C)
    p2.ch7(D, C)
    p2.ch8(D, C)
    p3.ch9(D, C)
    p3.ch10(D, C)
    p3.ch11(D, C)
    p4.ch12(D, C)
    p4.ch13(D, C)
    p4.ch14(D, C)
    p5.ch15(D, C)
    p4.ch16(D, C)
    p5.ch17_18(D, C)
    p4.refs(D, C)
    p5.appendix_cheatsheet(D, C)

    info = D.save(OUT)
    dump_json(info, REPORT / "report_build_info.json")
    LOG.info("saved %s", OUT)
    for k, v in info.items():
        LOG.info("  %s = %s", k, v)
    if info["non_times_new_roman_runs"]:
        raise AssertionError("non Times New Roman runs found: "
                             f"{info['non_times_new_roman_runs']}")
    print(f"\nOK  {OUT}")
    print(f"    paragraphs={info['n_paragraphs']}  tables={info['n_tables']}  "
          f"figures={info['n_figures']}  chars={info['n_characters']:,}")


if __name__ == "__main__":
    main()
