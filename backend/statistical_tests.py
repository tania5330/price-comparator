import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Tuple


def mann_whitney_test(scores1: List[float], scores2: List[float], model1_name: str = "Modelo 1", model2_name: str = "Modelo 2") -> Dict[str, Any]:
    """Mann-Whitney U test for comparing two models' performance."""
    stat, p_value = stats.mannwhitneyu(scores1, scores2, alternative="two-sided")
    alpha = 0.05
    mean1 = np.mean(scores1)
    mean2 = np.mean(scores2)
    if p_value > alpha:
        conclusion = f"No existe diferencia significativa entre {model1_name} y {model2_name} (p = {p_value:.4f})."
    else:
        if mean1 < mean2:
            conclusion = f"{model1_name} supera significativamente a {model2_name} (p = {p_value:.4f})."
        else:
            conclusion = f"{model2_name} supera significativamente a {model1_name} (p = {p_value:.4f})."

    return {
        "test": "Mann-Whitney U",
        "model1": model1_name,
        "model2": model2_name,
        "statistic": stat,
        "p_value": p_value,
        "alpha": alpha,
        "conclusion": conclusion,
        "scores1_mean": mean1,
        "scores2_mean": mean2,
    }


def kolmogorov_smirnov_test(errors1: List[float], errors2: List[float], model1_name: str = "Modelo 1", model2_name: str = "Modelo 2") -> Dict[str, Any]:
    """Kolmogorov-Smirnov test for comparing error distributions."""
    stat, p_value = stats.ks_2samp(errors1, errors2)
    alpha = 0.05
    conclusion = f"Las distribuciones de errores de {model1_name} y {model2_name} son similares (p = {p_value:.4f})." if p_value > alpha else f"Las distribuciones de errores de {model1_name} y {model2_name} son significativamente diferentes (p = {p_value:.4f})."

    return {
        "test": "Kolmogorov-Smirnov",
        "model1": model1_name,
        "model2": model2_name,
        "statistic": stat,
        "p_value": p_value,
        "alpha": alpha,
        "conclusion": conclusion,
    }


def morgan_pitman_test(errors1: List[float], errors2: List[float], model1_name: str = "Modelo 1", model2_name: str = "Modelo 2") -> Dict[str, Any]:
    """Morgan-Pitman test for comparing error variances (stability)."""
    if len(errors1) != len(errors2):
        raise ValueError("Both error arrays must have the same length")

    n = len(errors1)
    e1 = np.array(errors1)
    e2 = np.array(errors2)

    d = e1 - e2
    s = e1 + e2

    r, _ = stats.pearsonr(d, s)
    t_stat = r * np.sqrt((n - 2) / (1 - r ** 2)) if r != 0 else 0
    p_value = 2 * stats.t.sf(np.abs(t_stat), df=n - 2)

    alpha = 0.05
    var1 = np.var(errors1, ddof=1)
    var2 = np.var(errors2, ddof=1)

    if p_value > alpha:
        conclusion = f"No hay diferencia significativa en la estabilidad entre {model1_name} y {model2_name} (p = {p_value:.4f})."
    else:
        if var1 < var2:
            conclusion = f"{model1_name} es significativamente más estable que {model2_name} (p = {p_value:.4f})."
        else:
            conclusion = f"{model2_name} es significativamente más estable que {model1_name} (p = {p_value:.4f})."

    return {
        "test": "Morgan-Pitman",
        "model1": model1_name,
        "model2": model2_name,
        "statistic": t_stat,
        "p_value": p_value,
        "alpha": alpha,
        "variance1": var1,
        "variance2": var2,
        "conclusion": conclusion,
    }


def stability_analysis(scores: List[float]) -> Dict[str, Any]:
    """Analyze stability of a single model across multiple runs."""
    mean_score = np.mean(scores)
    std_score = np.std(scores, ddof=1)
    cv = (std_score / mean_score) * 100 if mean_score != 0 else float("inf")

    if cv < 5:
        stability_class = "Excelente"
    elif cv < 10:
        stability_class = "Alta"
    elif cv < 20:
        stability_class = "Media"
    else:
        stability_class = "Baja"

    return {
        "mean": mean_score,
        "std": std_score,
        "coefficient_of_variation": cv,
        "stability_class": stability_class,
    }


def friedman_test(scores_dict: Dict[str, List[float]]) -> Dict[str, Any]:
    """Friedman test for comparing multiple models' performance."""
    model_names = list(scores_dict.keys())
    scores_matrix = np.array([scores_dict[name] for name in model_names]).T
    n_samples, n_models = scores_matrix.shape

    if n_models < 3:
        raise ValueError("Friedman test requires at least 3 models")

    ranks = np.apply_along_axis(stats.rankdata, axis=1, arr=scores_matrix)
    mean_ranks = np.mean(ranks, axis=0)

    stat, p_value = stats.friedmanchisquare(*[scores_dict[name] for name in model_names])
    alpha = 0.05

    conclusion = "No hay diferencias significativas entre modelos" if p_value > alpha else "Hay diferencias significativas entre modelos"

    return {
        "test": "Friedman",
        "statistic": stat,
        "p_value": p_value,
        "alpha": alpha,
        "mean_ranks": dict(zip(model_names, mean_ranks)),
        "conclusion": conclusion,
    }


def nemenyi_posthoc_test(scores_dict: Dict[str, List[float]]) -> Dict[str, Any]:
    """Nemenyi post-hoc test after Friedman test to find which pairs differ."""
    model_names = list(scores_dict.keys())
    scores_matrix = np.array([scores_dict[name] for name in model_names]).T
    n_samples, n_models = scores_matrix.shape

    ranks = np.apply_along_axis(stats.rankdata, axis=1, arr=scores_matrix)
    mean_ranks = np.mean(ranks, axis=0)

    # Compute critical value (approximate for Nemenyi)
    q_critical = {
        3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850,
        7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164,
    }.get(n_models, 3.164)

    critical_diff = q_critical * np.sqrt(n_models * (n_models + 1) / (6 * n_samples))

    pairwise = []
    for i in range(n_models):
        for j in range(i + 1, n_models):
            diff = abs(mean_ranks[i] - mean_ranks[j])
            significant = diff > critical_diff
            pairwise.append({
                "model_1": model_names[i],
                "model_2": model_names[j],
                "rank_diff": diff,
                "critical_diff": critical_diff,
                "significant": significant,
            })

    return {
        "test": "Nemenyi",
        "model_names": model_names,
        "mean_ranks": dict(zip(model_names, mean_ranks)),
        "pairwise_tests": pairwise,
    }
