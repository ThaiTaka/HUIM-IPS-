"""Tên tiếng Việt của một cấu hình, luôn kèm minUtil θ (dùng chung cho hình, Word, PowerPoint).

Mã cấu hình (src/huim_multi.py):
  G_<m>__<θ>pct              HUIM chung, bộ định vị của bộ dữ liệu
  Z_<m>__<θ>pct              HUIM theo vùng / tầng
  T_<m>__<θ>pct, TZ_...      như G / Z nhưng bộ định vị chọn lại trên tập AP HUIM (bước 5)
  R_<m>__<θ>pct__<quy tắc>   quy tắc chọn AP trên tập HUI đầy đủ của EFIM (bước 6)
  E_<mean|median>__a+b(+c)   ensemble (bước 7)
"""
from hinh_chung import VUNG, theta_txt

QT = {"topn0.5": "top-n 50 %", "topn0.75": "top-n 75 %", "frequent2": "frequent ≥ 2",
      "frequentmedian": "frequent ≥ trung vị", "weighted0.5": "weighted γ = 0,5",
      "weighted1.0": "weighted γ = 1", "union": "union"}


def _parts(cfg: str):
    fam, rest = cfg.split("_", 1)
    m, rest = rest.split("__", 1)
    if "pct__" in rest:
        th, rule = rest.split("pct__")
    else:
        th, rule = rest.replace("pct", ""), None
    return fam, m, float(th), rule


def lbl(cfg: str, key: str, ngan: bool = False) -> str:
    cfg = str(cfg)
    vung = VUNG.get(key) or "vùng"
    if cfg.startswith("E_"):
        how, mem = cfg[2:].split("__", 1)
        h = ("TB" if ngan else "trung bình") if how == "mean" else "trung vị"
        return f"Ensemble {h}: " + " + ".join(lbl(x, key, ngan=True) for x in mem.split("+"))
    fam, m, th, rule = _parts(cfg)
    pham_vi = f"theo {vung}" if fam in ("Z", "TZ") else "chung"
    s = (f"{pham_vi.capitalize()} {m}, θ = {theta_txt(th)}" if ngan else
         f"HUIM {pham_vi}, Model {m}, θ = {theta_txt(th)}")
    if fam in ("T", "TZ"):
        s += ", định vị chọn lại" if ngan else ", bộ định vị chọn lại trên AP HUIM"
    if fam == "R":
        s += f", {QT.get(rule, rule)}" if ngan else f", quy tắc {QT.get(rule, rule)}"
    return s


def theta_cua(cfg: str) -> list[float]:
    cfg = str(cfg)
    mem = cfg.split("__", 1)[1].split("+") if cfg.startswith("E_") else [cfg]
    return [_parts(c)[2] for c in mem]
