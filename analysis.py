"""
E-commerce Checkout Redesign — A/B Test Statistical Analysis
Tests whether the new one-page checkout (B) changed conversion rate vs
the old multi-step checkout (A).

Methods used:
  1. Two-proportion z-test (hypothesis test + p-value)
  2. 95% confidence interval for the difference in conversion rates
  3. Effect size (Cohen's h)
"""

import numpy as np
import pandas as pd
from statsmodels.stats.proportion import (
    proportions_ztest,
    confint_proportions_2indep,
)

DATA_PATH = "/home/claude/ecommerce_checkout_ab_test/data/ab_test_checkout_data.csv"

df = pd.read_csv(DATA_PATH)

# ---- 1. Summary stats ----
summary = df.groupby("group")["converted"].agg(n="count", conversions="sum")
summary["conversion_rate"] = summary["conversions"] / summary["n"]
print("=== Group Summary ===")
print(summary, "\n")

n_a, n_b = summary.loc["A", "n"], summary.loc["B", "n"]
x_a, x_b = summary.loc["A", "conversions"], summary.loc["B", "conversions"]
p_a, p_b = summary.loc["A", "conversion_rate"], summary.loc["B", "conversion_rate"]

# ---- 2. Hypothesis test: two-proportion z-test ----
# H0: p_A = p_B   |   H1: p_A != p_B  (two-sided)
count = np.array([x_b, x_a])   # order: treatment, control
nobs = np.array([n_b, n_a])
z_stat, p_value = proportions_ztest(count, nobs, alternative="two-sided")

print("=== Hypothesis Test (Two-Proportion Z-Test) ===")
print(f"Z-statistic: {z_stat:.4f}")
print(f"P-value:     {p_value:.6f}")

alpha = 0.05
significant = p_value < alpha
print(f"Significant at alpha=0.05? {'YES' if significant else 'NO'}\n")

# ---- 3. Confidence interval for difference in proportions (B - A) ----
ci_low, ci_high = confint_proportions_2indep(
    count1=x_b, nobs1=n_b, count2=x_a, nobs2=n_a, method="wald"
)
diff = p_b - p_a
rel_lift = diff / p_a * 100

print("=== Confidence Interval (95%) for Difference (B - A) ===")
print(f"Absolute difference: {diff*100:.2f} percentage points")
print(f"Relative lift:       {rel_lift:.2f}%")
print(f"95% CI:              [{ci_low*100:.2f}pp, {ci_high*100:.2f}pp]")
print(f"CI excludes 0?       {'YES -> supports real effect' if ci_low > 0 or ci_high < 0 else 'NO'}\n")

# ---- 4. Effect size: Cohen's h ----
def cohens_h(p1, p2):
    phi1 = 2 * np.arcsin(np.sqrt(p1))
    phi2 = 2 * np.arcsin(np.sqrt(p2))
    return phi1 - phi2

h = cohens_h(p_b, p_a)
abs_h = abs(h)
if abs_h < 0.2:
    magnitude = "negligible"
elif abs_h < 0.5:
    magnitude = "small"
elif abs_h < 0.8:
    magnitude = "medium"
else:
    magnitude = "large"

print("=== Effect Size (Cohen's h) ===")
print(f"Cohen's h: {h:.4f}  ({magnitude} effect)\n")

# ---- 5. Save results for reuse (e.g., notebook, README) ----
results = {
    "n_a": int(n_a), "n_b": int(n_b),
    "x_a": int(x_a), "x_b": int(x_b),
    "p_a": float(p_a), "p_b": float(p_b),
    "z_stat": float(z_stat), "p_value": float(p_value),
    "alpha": alpha, "significant": bool(significant),
    "diff_pp": float(diff * 100), "rel_lift_pct": float(rel_lift),
    "ci_low_pp": float(ci_low * 100), "ci_high_pp": float(ci_high * 100),
    "cohens_h": float(h), "effect_magnitude": magnitude,
}

import json
with open("/home/claude/ecommerce_checkout_ab_test/results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Results saved to results.json")
