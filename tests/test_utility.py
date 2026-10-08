"""PHASE F - correctness of the preprocessing and of the three utility models.

The mutual-information estimator is checked against
`sklearn.metrics.mutual_info_score`, which computes MI between two label
arrays exactly (in nats), so it is an independent oracle for our bit-valued
histogram implementation.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sklearn.metrics import mutual_info_score

from preprocess_uji import (NOT_DETECTED, Q_MAX, RSSI_DOC_MAX, RSSI_DOC_MIN,
                            Preprocessor, fit_preprocessor, joint_label)
from utility_models import (N_STATES, RSSI_BINS, build_external_utility,
                            conditional_entropy_reduction, discretise,
                            mutual_information)

WAPS = ["WAP001", "WAP002", "WAP003", "WAP004"]


def _toy(rssi_rows, buildings, floors):
    d = {w: [r[k] for r in rssi_rows] for k, w in enumerate(WAPS)}
    d["BUILDINGID"] = buildings
    d["FLOOR"] = floors
    return pd.DataFrame(d)


TOY = _toy(
    [[-40, 100, -90, 100],
     [-104, -60, 100, 100],
     [0, 100, -70, -80],
     [100, 100, 100, -104],
     [-55, -95, -65, 100],
     [100, -75, 100, -30]],
    buildings=[0, 0, 1, 1, 2, 2],
    floors=[0, 1, 0, 1, 0, 1])


# ------------------------------------------------------------- preprocessing
def test_fit_only_uses_documented_range_and_records_provenance():
    prep = fit_preprocessor(TOY)
    assert prep.wap_cols == WAPS
    assert prep.rssi_min_train == -104 and prep.rssi_max_train == 0
    assert prep.as_dict()["fitted_on"] == "trainingData.csv ONLY"
    assert RSSI_DOC_MIN <= prep.rssi_min_train <= prep.rssi_max_train <= RSSI_DOC_MAX


def test_fit_rejects_values_outside_documented_rssi_range():
    bad = TOY.copy()
    bad.loc[0, "WAP001"] = -200          # impossible RSSI, must be caught
    with pytest.raises(ValueError):
        fit_preprocessor(bad)


def test_positive_representation_semantics():
    """The sentinel must become 0, the weakest detection 1, the strongest Q_MAX.
    This is the single most important preprocessing property: raw 100 is
    numerically the LARGEST value in the matrix while meaning 'no signal'."""
    prep = fit_preprocessor(TOY)
    X = prep.positive_representation(TOY)
    W = TOY[WAPS].to_numpy()
    assert np.all(X[W == NOT_DETECTED] == 0.0)
    assert np.all(X[W != NOT_DETECTED] >= 1.0)
    assert X[W == -104][0] == pytest.approx(1.0)
    assert X[W == 0][0] == pytest.approx(float(Q_MAX))
    # monotone in RSSI
    assert X[4, 0] > X[0, 2]          # -55 dBm stronger than -90 dBm


def test_internal_utility_is_positive_integer_exactly_where_detected():
    prep = fit_preprocessor(TOY)
    Q = prep.internal_utility_matrix(TOY)
    W = TOY[WAPS].to_numpy()
    assert Q.dtype == np.int64
    assert np.all(Q[W == NOT_DETECTED] == 0)
    assert np.all(Q[W != NOT_DETECTED] >= 1)
    assert Q.max() <= Q_MAX


def test_transactions_contain_exactly_the_detected_waps():
    prep = fit_preprocessor(TOY)
    txs, counts = prep.transactions(TOY)
    W = TOY[WAPS].to_numpy()
    assert len(txs) == len(TOY)
    for r, t in enumerate(txs):
        expected = {WAPS[j] for j in range(len(WAPS)) if W[r, j] != NOT_DETECTED}
        assert set(t) == expected
        assert all(v >= 1 for v in t.values())
    assert list(counts) == [(W[r] != NOT_DETECTED).sum() for r in range(len(TOY))]


def test_empty_fingerprint_becomes_empty_transaction():
    df = _toy([[100, 100, 100, 100], [-50, -60, 100, 100]], [0, 0], [0, 0])
    prep = Preprocessor(WAPS, -104.0, 0.0, 2)
    txs, counts = prep.transactions(df)
    assert txs[0] == {} and counts[0] == 0
    assert len(txs[1]) == 2


def test_joint_label():
    y = joint_label(TOY)
    assert list(y) == ["0_0", "0_1", "1_0", "1_1", "2_0", "2_1"]


# ---------------------------------------------------------------- discretise
def test_discretise_state_semantics():
    S = discretise(TOY, WAPS)
    W = TOY[WAPS].to_numpy()
    assert S.shape == W.shape
    # state 0 is reserved for "not detected"
    assert np.all(S[W == NOT_DETECTED] == 0)
    assert np.all(S[W != NOT_DETECTED] >= 1)
    assert S.max() <= N_STATES - 1
    # boundary values land in the intended bins
    assert S[1, 0] == 1            # -104 dBm -> weakest bin
    assert S[2, 0] == N_STATES - 1  # 0 dBm -> strongest bin


def test_discretise_is_monotone_in_signal_strength():
    df = _toy([[-104, -95, -85, -75], [-65, -30, 0, -100]], [0, 1], [0, 1])
    S = discretise(df, WAPS)
    vals = df[WAPS].to_numpy().ravel()
    states = S.ravel()
    order = np.argsort(vals)
    assert np.all(np.diff(states[order]) >= 0)


# ------------------------------------------------------- mutual information
@pytest.mark.parametrize("seed", list(range(25)))
def test_mutual_information_matches_sklearn_oracle(seed):
    """sklearn.metrics.mutual_info_score computes MI exactly, in nats."""
    rng = np.random.default_rng(seed)
    n, m = rng.integers(40, 400), 6
    states = rng.integers(0, N_STATES, size=(n, m)).astype(np.int8)
    y = rng.integers(0, 13, size=n).astype(str)
    mine = mutual_information(states, y)
    for j in range(m):
        oracle = mutual_info_score(states[:, j], y) / np.log(2.0)
        assert mine[j] == pytest.approx(oracle, abs=1e-9), f"col {j}"


def test_mi_is_zero_for_a_constant_feature():
    states = np.zeros((50, 1), dtype=np.int8)
    y = np.array(["a", "b"] * 25)
    assert mutual_information(states, y)[0] == pytest.approx(0.0, abs=1e-12)


def test_mi_equals_label_entropy_for_a_perfect_predictor():
    y = np.array(["a"] * 20 + ["b"] * 20 + ["c"] * 20)
    states = np.where(y == "a", 0, np.where(y == "b", 1, 2)).astype(np.int8)[:, None]
    mi, h_y = conditional_entropy_reduction(states, y)
    assert h_y == pytest.approx(np.log2(3), abs=1e-9)
    assert mi[0] == pytest.approx(h_y, abs=1e-9)


def test_mi_never_exceeds_label_entropy():
    rng = np.random.default_rng(99)
    states = rng.integers(0, N_STATES, size=(500, 20)).astype(np.int8)
    y = rng.integers(0, 13, size=500).astype(str)
    mi, h_y = conditional_entropy_reduction(states, y)
    assert np.all(mi >= -1e-12)
    assert np.all(mi <= h_y + 1e-9)


# ---------------------------------------------------------- utility models
def test_model_a_is_the_constant_control():
    prep = fit_preprocessor(TOY)
    m = build_external_utility("A", TOY, prep, joint_label(TOY), "training")
    assert set(m.external_utility.values()) == {1.0}
    assert m.name == "A_signal"


def test_model_b_and_c_produce_strictly_positive_bounded_p():
    prep = fit_preprocessor(TOY)
    y = joint_label(TOY)
    for code in ("B", "C"):
        m = build_external_utility(code, TOY, prep, y, "training")
        vals = np.array(list(m.external_utility.values()))
        assert np.all(vals > 0), f"model {code} produced a non-positive p"
        assert vals.max() == pytest.approx(1.0)
        assert len(m.external_utility) == len(WAPS)


def test_model_b_weights_track_mutual_information():
    prep = fit_preprocessor(TOY)
    y = joint_label(TOY)
    m = build_external_utility("B", TOY, prep, y, "training")
    mi = mutual_information(discretise(TOY, WAPS), y)
    order_mi = np.argsort(-mi)
    p = np.array([m.external_utility[w] for w in WAPS])
    order_p = np.argsort(-p)
    assert list(order_mi) == list(order_p)


def test_leakage_gate_refuses_non_training_split():
    """The single most important guard in the project."""
    prep = fit_preprocessor(TOY)
    y = joint_label(TOY)
    for code in ("A", "B", "C"):
        with pytest.raises(ValueError, match="data leakage"):
            build_external_utility(code, TOY, prep, y, "validation")
        with pytest.raises(ValueError):
            build_external_utility(code, TOY, prep, y, "test")


def test_total_database_utility_equals_sum_of_transaction_utilities():
    prep = fit_preprocessor(TOY)
    y = joint_label(TOY)
    txs, _ = prep.transactions(TOY)
    for code in ("A", "B", "C"):
        m = build_external_utility(code, TOY, prep, y, "training")
        assert m.total_database_utility(txs) == pytest.approx(
            float(m.transaction_utilities(txs).sum()))


def test_model_a_total_utility_is_the_sum_of_internal_utilities():
    prep = fit_preprocessor(TOY)
    txs, _ = prep.transactions(TOY)
    m = build_external_utility("A", TOY, prep, joint_label(TOY), "training")
    assert m.total_database_utility(txs) == float(
        prep.internal_utility_matrix(TOY).sum())


def test_unknown_model_code_raises():
    prep = fit_preprocessor(TOY)
    with pytest.raises(ValueError):
        build_external_utility("Z", TOY, prep, joint_label(TOY), "training")


def test_utility_models_are_accepted_by_efim():
    """End-to-end: the (q,p) pairs this module produces must satisfy EFIM's
    positivity precondition and agree with brute force on the toy database."""
    from huim.brute_force import brute_force_hui, total_utility
    from huim.efim import mine_efim
    prep = fit_preprocessor(TOY)
    y = joint_label(TOY)
    txs, _ = prep.transactions(TOY)
    txs = [t for t in txs if t]
    for code in ("A", "B", "C"):
        m = build_external_utility(code, TOY, prep, y, "training")
        tot = total_utility(txs, m.external_utility)
        for frac in (0.5, 0.2, 0.05):
            mu = tot * frac
            huis, stats = mine_efim(txs, m.external_utility, min_util=mu)
            exp = brute_force_hui(txs, m.external_utility, mu)
            assert {frozenset(x): round(u, 6) for x, u, _ in huis} == \
                   {frozenset(x): round(u, 6) for x, u, _ in exp}, (code, frac)
            assert stats.status == "COMPLETED"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
