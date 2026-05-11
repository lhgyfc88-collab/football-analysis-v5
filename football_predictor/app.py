from pathlib import Path

import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
MATCHES_CSV = BASE_DIR / "matches.csv"

SAMPLE_MATCHES = [
    {
        "date": "2026-05-11 19:30",
        "league": "英超",
        "home_team": "Manchester City",
        "away_team": "Chelsea",
        "odds_home": 1.72,
        "odds_draw": 3.85,
        "odds_away": 4.80,
        "opening_home": 1.80,
        "opening_draw": 3.70,
        "opening_away": 4.50,
        "handicap_open": -0.75,
        "handicap_now": -1.00,
        "home_score": 2,
        "away_score": 1,
    },
    {
        "date": "2026-05-11 20:00",
        "league": "西甲",
        "home_team": "Real Madrid",
        "away_team": "Villarreal",
        "odds_home": 1.58,
        "odds_draw": 4.10,
        "odds_away": 5.60,
        "opening_home": 1.64,
        "opening_draw": 4.00,
        "opening_away": 5.20,
        "handicap_open": -1.00,
        "handicap_now": -1.25,
        "home_score": 2,
        "away_score": 0,
    },
    {
        "date": "2026-05-11 20:45",
        "league": "意甲",
        "home_team": "Inter Milan",
        "away_team": "Roma",
        "odds_home": 2.05,
        "odds_draw": 3.35,
        "odds_away": 3.65,
        "opening_home": 2.15,
        "opening_draw": 3.25,
        "opening_away": 3.45,
        "handicap_open": -0.25,
        "handicap_now": -0.50,
        "home_score": 1,
        "away_score": 1,
    },
    {
        "date": "2026-05-11 21:00",
        "league": "德甲",
        "home_team": "Dortmund",
        "away_team": "Leverkusen",
        "odds_home": 2.70,
        "odds_draw": 3.55,
        "odds_away": 2.46,
        "opening_home": 2.55,
        "opening_draw": 3.50,
        "opening_away": 2.60,
        "handicap_open": 0.00,
        "handicap_now": 0.25,
        "home_score": 1,
        "away_score": 2,
    },
    {
        "date": "2026-05-11 22:00",
        "league": "法甲",
        "home_team": "Paris Saint-Germain",
        "away_team": "Lyon",
        "odds_home": 1.68,
        "odds_draw": 3.95,
        "odds_away": 4.90,
        "opening_home": 1.75,
        "opening_draw": 3.75,
        "opening_away": 4.65,
        "handicap_open": -0.75,
        "handicap_now": -1.00,
        "home_score": 3,
        "away_score": 1,
    },
]

COLUMN_ALIASES = {
    "日期": "date",
    "联盟": "league",
    "主队": "home_team",
    "主场_球队": "home_team",
    "客队": "away_team",
    "客场_球队": "away_team",
    "概率H": "prob_H",
    "概率D": "prob_D",
    "概率A": "prob_A",
    "目标差异": "target_diff",
    "主场优势": "home_adv",
}


def load_matches() -> pd.DataFrame:
    """Load user CSV data when present; otherwise use built-in demo fixtures."""
    if MATCHES_CSV.exists():
        df = pd.read_csv(MATCHES_CSV)
        df = df.rename(columns={k: v for k, v in COLUMN_ALIASES.items() if k in df.columns})
    else:
        df = pd.DataFrame(SAMPLE_MATCHES)

    required_defaults = {
        "date": "待定",
        "league": "未分类联赛",
        "home_team": "主队",
        "away_team": "客队",
        "home_score": 0,
        "away_score": 0,
        "odds_home": 2.0,
        "odds_draw": 3.2,
        "odds_away": 3.5,
        "opening_home": None,
        "opening_draw": None,
        "opening_away": None,
        "handicap_open": 0.0,
        "handicap_now": 0.0,
    }
    for column, default in required_defaults.items():
        if column not in df.columns:
            df[column] = default

    numeric_columns = [
        "home_score",
        "away_score",
        "odds_home",
        "odds_draw",
        "odds_away",
        "opening_home",
        "opening_draw",
        "opening_away",
        "handicap_open",
        "handicap_now",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["opening_home"] = df["opening_home"].fillna(df["odds_home"])
    df["opening_draw"] = df["opening_draw"].fillna(df["odds_draw"])
    df["opening_away"] = df["opening_away"].fillna(df["odds_away"])

    return enrich_matches(df)


def normalize_probabilities(row: pd.Series) -> tuple[float, float, float]:
    if all(col in row.index and pd.notna(row[col]) for col in ["prob_H", "prob_D", "prob_A"]):
        values = [float(row["prob_H"]), float(row["prob_D"]), float(row["prob_A"])]
        if max(values) > 1:
            values = [value / 100 for value in values]
        total = sum(values)
        if total > 0:
            return tuple(value / total for value in values)

    implied = [1 / max(float(row[col]), 1.01) for col in ["odds_home", "odds_draw", "odds_away"]]
    total = sum(implied)
    return tuple(value / total for value in implied)


def risk_level(upset_index: float, kelly_home: float, kelly_draw: float, kelly_away: float) -> str:
    max_kelly = max(kelly_home, kelly_draw, kelly_away)
    if upset_index >= 68 or max_kelly >= 1.08:
        return "高风险"
    if upset_index >= 48 or max_kelly >= 1.00:
        return "中风险"
    return "低风险"


def format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def enrich_matches(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        for column in [
            "prob_H",
            "prob_D",
            "prob_A",
            "target_diff",
            "home_adv",
            "prediction",
            "score_prediction",
            "half_full",
            "upset_index",
            "handicap_change",
            "kelly_H",
            "kelly_D",
            "kelly_A",
            "risk_level",
            "bankroll_advice",
            "combo_3x1",
            "combo_3x4",
        ]:
            df[column] = []
        return df

    probabilities = df.apply(normalize_probabilities, axis=1, result_type="expand")
    df[["prob_H", "prob_D", "prob_A"]] = probabilities

    df["target_diff"] = df["prob_H"] - df["prob_A"]
    df["home_adv"] = 1 + df["target_diff"].clip(lower=-0.25, upper=0.25)

    df["prediction"] = df[["prob_H", "prob_D", "prob_A"]].idxmax(axis=1).map(
        {"prob_H": "主胜", "prob_D": "平局", "prob_A": "客胜"}
    )
    df["score_prediction"] = df.apply(predict_score, axis=1)
    df["half_full"] = df.apply(predict_half_full, axis=1)

    df["upset_index"] = df.apply(
        lambda row: round((1 - max(row["prob_H"], row["prob_D"], row["prob_A"])) * 100 + abs(row["odds_home"] - row["opening_home"]) * 7, 1),
        axis=1,
    )
    df["handicap_change"] = df.apply(
        lambda row: f"{row['handicap_open']:+.2f} → {row['handicap_now']:+.2f}", axis=1
    )
    df["kelly_H"] = df["prob_H"] * df["odds_home"]
    df["kelly_D"] = df["prob_D"] * df["odds_draw"]
    df["kelly_A"] = df["prob_A"] * df["odds_away"]
    df["risk_level"] = df.apply(
        lambda row: risk_level(row["upset_index"], row["kelly_H"], row["kelly_D"], row["kelly_A"]), axis=1
    )
    df["bankroll_advice"] = df.apply(bankroll_advice, axis=1)
    df["combo_3x1"] = df.apply(lambda row: combo_pick(row, conservative=False), axis=1)
    df["combo_3x4"] = df.apply(lambda row: combo_pick(row, conservative=True), axis=1)

    for column in ["prob_H", "prob_D", "prob_A"]:
        df[f"{column}_text"] = df[column].apply(format_pct)
    for column in ["kelly_H", "kelly_D", "kelly_A", "target_diff", "home_adv"]:
        df[f"{column}_text"] = df[column].apply(lambda value: f"{value:.2f}")

    return df


def predict_score(row: pd.Series) -> str:
    home_strength = row["prob_H"] + row["prob_D"] * 0.35
    away_strength = row["prob_A"] + row["prob_D"] * 0.30
    home_goals = min(4, max(0, round(home_strength * 3.1 + 0.25)))
    away_goals = min(4, max(0, round(away_strength * 2.7)))
    if row["prediction"] == "平局":
        balanced_goal = max(1, round((home_goals + away_goals) / 2))
        home_goals = away_goals = balanced_goal
    return f"{home_goals}-{away_goals}"


def predict_half_full(row: pd.Series) -> str:
    if row["prediction"] == "主胜":
        return "平/主" if row["prob_H"] < 0.50 else "主/主"
    if row["prediction"] == "客胜":
        return "平/客" if row["prob_A"] < 0.50 else "客/客"
    return "平/平"


def bankroll_advice(row: pd.Series) -> str:
    if row["risk_level"] == "低风险":
        return "单场 3%-5% 仓位，可做串关核心"
    if row["risk_level"] == "中风险":
        return "单场 1%-2% 仓位，建议搭配防平/防冷"
    return "≤1% 观察仓位，优先进入容错结构"


def combo_pick(row: pd.Series, conservative: bool) -> str:
    primary = row["prediction"]
    if not conservative:
        return primary

    probabilities = {"主胜": row["prob_H"], "平局": row["prob_D"], "客胜": row["prob_A"]}
    ordered = sorted(probabilities, key=probabilities.get, reverse=True)
    return "/".join(ordered[:2]) if row["risk_level"] != "低风险" else ordered[0]


@app.route("/")
def index():
    df = load_matches()
    leagues = sorted(df["league"].dropna().unique())
    strongest_index = df[["prob_H", "prob_D", "prob_A"]].max(axis=1).idxmax() if not df.empty else None
    summary = {
        "total_matches": len(df),
        "low_risk": int((df["risk_level"] == "低风险").sum()),
        "avg_upset": f"{df['upset_index'].mean():.1f}" if not df.empty else "0.0",
        "top_pick": df.loc[strongest_index, "prediction"] if strongest_index is not None else "-",
    }
    return render_template(
        "index.html",
        data=df.to_dict(orient="records"),
        leagues=leagues,
        summary=summary,
    )


if __name__ == "__main__":
    app.run(debug=True)
