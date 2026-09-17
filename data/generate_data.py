"""
Simulates a realistic e-commerce checkout A/B test dataset.

Scenario:
- Control (A): old multi-step checkout
- Treatment (B): new redesigned one-page checkout
- True underlying conversion rates are set intentionally so the redesign
  has a real, modest positive effect (mirrors typical real-world UX lifts).
"""

import numpy as np
import pandas as pd

np.random.seed(42)

N_PER_GROUP = 6000

# True (unknown-to-analyst) conversion rates baked into the simulation
TRUE_CR_CONTROL = 0.120     # 12.0% baseline conversion
TRUE_CR_TREATMENT = 0.138   # 13.8% -> a realistic ~1.8pp / 15% relative lift

DEVICE_TYPES = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS = [0.58, 0.34, 0.08]

TRAFFIC_SOURCES = ["organic", "paid_search", "social", "email", "direct"]
TRAFFIC_WEIGHTS = [0.30, 0.25, 0.15, 0.15, 0.15]


def simulate_group(group_label, n, true_cr):
    device = np.random.choice(DEVICE_TYPES, size=n, p=DEVICE_WEIGHTS)
    traffic = np.random.choice(TRAFFIC_SOURCES, size=n, p=TRAFFIC_WEIGHTS)

    # Slight realistic variation: mobile converts a bit lower, desktop a bit higher
    device_adj = np.select(
        [device == "mobile", device == "desktop", device == "tablet"],
        [-0.01, 0.015, 0.0],
    )
    conv_prob = np.clip(true_cr + device_adj, 0.01, 0.99)
    converted = np.random.binomial(1, conv_prob)

    session_duration = np.round(
        np.random.gamma(shape=4.0, scale=45, size=n) + (converted * 20), 1
    )  # seconds; converters browse a bit longer on average

    cart_value = np.round(
        np.where(converted == 1, np.random.gamma(shape=3.0, scale=18, size=n), 0), 2
    )

    user_ids = [f"{group_label}_{i:06d}" for i in range(n)]

    return pd.DataFrame(
        {
            "user_id": user_ids,
            "group": group_label,
            "device_type": device,
            "traffic_source": traffic,
            "session_duration_sec": session_duration,
            "converted": converted,
            "cart_value_usd": cart_value,
        }
    )


df_control = simulate_group("A", N_PER_GROUP, TRUE_CR_CONTROL)
df_treatment = simulate_group("B", N_PER_GROUP, TRUE_CR_TREATMENT)

df = pd.concat([df_control, df_treatment], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

out_path = "/home/claude/ecommerce_checkout_ab_test/data/ab_test_checkout_data.csv"
df.to_csv(out_path, index=False)

print(f"Saved {len(df)} rows to {out_path}")
print(df.groupby("group")["converted"].agg(["count", "sum", "mean"]))
