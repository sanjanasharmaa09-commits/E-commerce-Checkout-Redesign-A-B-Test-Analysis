import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

plt.rcParams["font.family"] = "DejaVu Sans"

DATA_PATH = "/home/claude/ecommerce_checkout_ab_test/data/ab_test_checkout_data.csv"
RESULTS_PATH = "/home/claude/ecommerce_checkout_ab_test/results.json"
VIS_DIR = "/home/claude/ecommerce_checkout_ab_test/visuals"

df = pd.read_csv(DATA_PATH)
with open(RESULTS_PATH) as f:
    r = json.load(f)

summary = df.groupby("group")["converted"].agg(n="count", conversions="sum")
summary["rate"] = summary["conversions"] / summary["n"]

# 95% CI per group (individual, Wilson method) for the error bars
cis = {}
for g in ["A", "B"]:
    low, high = proportion_confint(
        summary.loc[g, "conversions"], summary.loc[g, "n"], alpha=0.05, method="wilson"
    )
    cis[g] = (low, high)

# ---- Chart 1: Conversion rate comparison with 95% CI error bars ----
fig, ax = plt.subplots(figsize=(7, 5))
groups = ["A\n(Old Checkout)", "B\n(New Checkout)"]
rates = [summary.loc["A", "rate"] * 100, summary.loc["B", "rate"] * 100]
errors = [
    [(summary.loc[g, "rate"] - cis[g][0]) * 100 for g in ["A", "B"]],
    [(cis[g][1] - summary.loc[g, "rate"]) * 100 for g in ["A", "B"]],
]

bars = ax.bar(groups, rates, color=["#4C4C4C", "#1F6FEB"], width=0.5, yerr=errors,
               capsize=8, error_kw={"linewidth": 1.5, "ecolor": "black"})

for bar, rate in zip(bars, rates):
    ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.6, f"{rate:.2f}%",
            ha="center", fontsize=11, fontweight="bold")

ax.set_ylabel("Conversion Rate (%)")
ax.set_title("Checkout Redesign: Conversion Rate by Group\n(error bars = 95% CI)",
              fontsize=12, fontweight="bold")
ax.set_ylim(0, max(rates) + 4)

annotation = (
    f"p-value = {r['p_value']:.4f}  |  "
    f"Diff = {r['diff_pp']:.2f}pp  |  "
    f"95% CI of diff = [{r['ci_low_pp']:.2f}, {r['ci_high_pp']:.2f}]pp"
)
ax.text(0.5, -0.18, annotation, transform=ax.transAxes, ha="center", fontsize=9,
        color="#333333")

plt.tight_layout()
plt.savefig(f"{VIS_DIR}/conversion_rate_comparison.png", dpi=150)
plt.close()

# ---- Chart 2: Conversion rate by device type, split by group ----
device_summary = (
    df.groupby(["device_type", "group"])["converted"].mean().reset_index()
)
device_pivot = device_summary.pivot(index="device_type", columns="group", values="converted") * 100
device_pivot = device_pivot.reindex(["mobile", "desktop", "tablet"])

fig, ax = plt.subplots(figsize=(7.5, 5))
x = np.arange(len(device_pivot.index))
width = 0.35
ax.bar(x - width/2, device_pivot["A"], width, label="A (Old)", color="#4C4C4C")
ax.bar(x + width/2, device_pivot["B"], width, label="B (New)", color="#1F6FEB")
ax.set_xticks(x)
ax.set_xticklabels([d.capitalize() for d in device_pivot.index])
ax.set_ylabel("Conversion Rate (%)")
ax.set_title("Conversion Rate by Device Type", fontsize=12, fontweight="bold")
ax.legend()
plt.tight_layout()
plt.savefig(f"{VIS_DIR}/conversion_by_device.png", dpi=150)
plt.close()

print("Saved charts to", VIS_DIR)
