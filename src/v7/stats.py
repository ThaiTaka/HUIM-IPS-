"""Confidence intervals that respect the grouping of the data.

Fingerprints of one phone (and one collection session) are strongly correlated, so a query-level bootstrap
would give intervals that are too narrow. These helpers resample whole groups (PHONEID by default) with
replacement; the statistic of every replicate is computed on the pooled queries of the sampled groups.
"""
from __future__ import annotations

import numpy as np


def _group_sums(values: np.ndarray, groups: np.ndarray):
    ug, inv = np.unique(groups, return_inverse=True)
    s = np.bincount(inv, weights=values, minlength=len(ug))
    c = np.bincount(inv, minlength=len(ug)).astype(float)
    return s, c


def cluster_bootstrap_mean(e: np.ndarray, groups: np.ndarray, n_boot: int = 4000, seed: int = 0, alpha: float = 0.05):
    """Mean of `e` with a percentile interval from resampling groups. Returns (mean, lo, hi)."""
    s, c = _group_sums(e, groups)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), (n_boot, len(s)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return float(e.mean()), float(np.quantile(m, alpha / 2)), float(np.quantile(m, 1 - alpha / 2))


def paired_cluster_bootstrap(e_new: np.ndarray, e_ref: np.ndarray, groups: np.ndarray, n_boot: int = 4000, seed: int = 0,
                             alpha: float = 0.05):
    """Mean difference (new - reference) on the same queries with a group-resampled interval, and the share of
    replicates in which `new` is better (lower mean). Returns (diff, lo, hi, p_better)."""
    d = e_new - e_ref
    s, c = _group_sums(d, groups)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), (n_boot, len(s)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return float(d.mean()), float(np.quantile(m, alpha / 2)), float(np.quantile(m, 1 - alpha / 2)), float((m < 0).mean())
