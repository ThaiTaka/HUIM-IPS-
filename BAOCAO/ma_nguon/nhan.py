"""Tên ngắn tiếng Việt của một cấu hình, luôn kèm minUtil θ (dùng chung cho Word và PowerPoint)."""
from hinh_chung import theta_txt


def lbl(cfg: str) -> str:
    cfg = str(cfg)
    if cfg.startswith("E_"):
        how, mem = cfg[2:].split("__", 1)
        return ("Ensemble " + ("trung bình" if how == "mean" else "trung vị") + ": "
                + " + ".join(lbl(x) for x in mem.split("+")))
    if cfg.startswith("R_"):
        rest = cfg[2:]
        scope, rest = rest.split("_", 1)
        mm, rest = rest.split("__", 1)
        th, rule = rest.split("pct__")
        return (f"{'HUIM theo tòa' if scope == 'PB' else 'HUIM chung'}, Model {mm}, "
                f"θ = {theta_txt(float(th))}, quy tắc {rule}")
    scope, rest = cfg.split("_", 1)
    mm, th = rest.split("__")
    return (f"{'HUIM theo tòa' if scope == 'PB' else 'HUIM chung'}, Model {mm}, "
            f"θ = {theta_txt(float(th.replace('pct', '')))}")


def thanh_vien(cfg: str) -> list[tuple[str, str, float]]:
    """(phạm vi 'G'/'PB', model, θ) của từng thành viên một ensemble (hoặc của chính cấu hình)."""
    cfg = str(cfg)
    mem = cfg.split("__", 1)[1].split("+") if cfg.startswith("E_") else [cfg]
    out = []
    for c in mem:
        c = c[2:] if c.startswith("R_") else c
        scope, rest = c.split("_", 1)
        mm, th = rest.split("__")[:2]
        out.append((scope, mm, float(th.replace("pct", ""))))
    return out


def lbl_ngan(cfg: str) -> str:
    """Bản ngắn cho nhãn trên hình; ensemble cùng θ được gộp: 'Ensemble trung vị: Chung C +
    Theo tòa B + Chung B, θ = 0,5 %'."""
    cfg = str(cfg)
    if cfg.startswith("E_"):
        tv = thanh_vien(cfg)
        how = "trung vị" if cfg.startswith("E_median") else "TB"
        if len({t for _, _, t in tv}) == 1:
            return (f"Ensemble {how}: " + " + ".join(
                f"{'Theo tòa' if s == 'PB' else 'Chung'} {m}" for s, m, _ in tv)
                + f", θ = {theta_txt(tv[0][2])}")
    return (lbl(cfg).replace("HUIM theo tòa", "Theo tòa").replace("HUIM chung", "Chung")
            .replace("Model ", "").replace("Ensemble trung bình", "Ensemble TB")
            .replace("quy tắc ", ""))
