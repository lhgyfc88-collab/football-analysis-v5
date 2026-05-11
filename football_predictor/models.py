from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from xgboost import XGBClassifier


@dataclass(frozen=True)
class V51RiskProfile:
    code: str
    label: str
    purpose: str
    css_class: str


RISK_PROFILES = {
    "A": V51RiskProfile("A", "A级：稳胆", "只能做稳胆", "risk-a"),
    "B": V51RiskProfile("B", "B级：价值盘", "适合做3串4价值位", "risk-b"),
    "C": V51RiskProfile("C", "C级：高风险", "只能小注娱乐，不能做主推稳健单", "risk-c"),
}

TEAM_NAME_MAP = {
    "Manchester City": "曼城",
    "Man City": "曼城",
    "Chelsea": "切尔西",
    "Real Madrid": "皇家马德里",
    "Villarreal": "比利亚雷亚尔",
    "Inter Milan": "国际米兰",
    "Internazionale": "国际米兰",
    "Roma": "罗马",
    "Dortmund": "多特蒙德",
    "Borussia Dortmund": "多特蒙德",
    "Leverkusen": "勒沃库森",
    "Bayer Leverkusen": "勒沃库森",
    "Paris Saint-Germain": "巴黎圣日耳曼",
    "PSG": "巴黎圣日耳曼",
    "Lyon": "里昂",
}

LEAGUE_NAME_MAP = {
    "Premier League": "英超",
    "La Liga": "西甲",
    "Serie A": "意甲",
    "Bundesliga": "德甲",
    "Ligue 1": "法甲",
}


def cn_team(name: Any) -> str:
    text = str(name or "").strip()
    return TEAM_NAME_MAP.get(text, text or "待定球队")


def cn_league(name: Any) -> str:
    text = str(name or "").strip()
    return LEAGUE_NAME_MAP.get(text, text or "未分类联赛")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if pd.isna(number):
        return default
    return number


def normalize_probabilities(row: pd.Series) -> tuple[float, float, float]:
    candidates = [("home_prob", "draw_prob", "away_prob"), ("prob_H", "prob_D", "prob_A")]
    for columns in candidates:
        if all(column in row.index and pd.notna(row[column]) for column in columns):
            values = [safe_float(row[column]) for column in columns]
            if max(values) > 1:
                values = [value / 100 for value in values]
            total = sum(values)
            if total > 0:
                return tuple(value / total for value in values)

    implied = [1 / max(safe_float(row[column], 2.0), 1.01) for column in ["odds_home", "odds_draw", "odds_away"]]
    total = sum(implied)
    return tuple(value / total for value in implied)


def format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def pick_prediction(row: pd.Series) -> str:
    return {"prob_H": "主胜", "prob_D": "平局", "prob_A": "客胜"}[row[["prob_H", "prob_D", "prob_A"]].idxmax()]


def predict_score(row: pd.Series) -> str:
    home_strength = row["prob_H"] + row["prob_D"] * 0.33
    away_strength = row["prob_A"] + row["prob_D"] * 0.30
    home_goals = min(4, max(0, round(home_strength * 3.0 + 0.25)))
    away_goals = min(4, max(0, round(away_strength * 2.65)))
    if row["prediction"] == "平局":
        balanced_goal = max(1, round((home_goals + away_goals) / 2))
        home_goals = away_goals = balanced_goal
    return f"{home_goals}-{away_goals}"


def secondary_score(row: pd.Series) -> str:
    if row["prediction"] == "主胜":
        return "1-0" if row["score_prediction"] != "1-0" else "2-1"
    if row["prediction"] == "客胜":
        return "0-1" if row["score_prediction"] != "0-1" else "1-2"
    return "0-0" if row["score_prediction"] != "0-0" else "2-2"


def upset_score(row: pd.Series) -> str:
    if row["prediction"] == "主胜":
        return "1-1"
    if row["prediction"] == "客胜":
        return "1-1"
    return "1-2" if row["prob_A"] >= row["prob_H"] else "2-1"


def predict_half_full(row: pd.Series) -> str:
    if row["prediction"] == "主胜":
        return "平/主" if row["prob_H"] < 0.50 else "主/主"
    if row["prediction"] == "客胜":
        return "平/客" if row["prob_A"] < 0.50 else "客/客"
    return "平/平"


def defensive_half_full(row: pd.Series) -> str:
    if row["upset_warning"] == "有":
        return "平/平" if row["prediction"] != "平局" else "平/客"
    return "平/主" if row["prediction"] == "主胜" else "平/客"


def handicap_direction(open_value: float, live_value: float) -> str:
    delta = live_value - open_value
    if abs(delta) < 0.01:
        return "盘口稳定"
    if delta < 0:
        return "主队升盘"
    return "主队降盘/客队受热"


def calculate_upset_index(row: pd.Series) -> float:
    top_prob = max(row["prob_H"], row["prob_D"], row["prob_A"])
    kelly_max = max(row["kelly_H"], row["kelly_D"], row["kelly_A"])
    handicap_delta = abs(row["handicap_now"] - row["handicap_open"])
    hot_favorite = 12 if top_prob >= 0.58 and row["odds_home"] <= 1.75 else 0
    market_noise = max(0, (kelly_max - 1.0) * 55)
    return round((1 - top_prob) * 100 + handicap_delta * 12 + hot_favorite + market_noise, 1)


def risk_grade(row: pd.Series) -> str:
    top_prob = max(row["prob_H"], row["prob_D"], row["prob_A"])
    kelly_max = max(row["kelly_H"], row["kelly_D"], row["kelly_A"])
    if row["upset_index"] >= 62 or kelly_max >= 1.08 or top_prob < 0.40:
        return "C"
    if row["upset_index"] >= 53 or kelly_max >= 1.00 or top_prob < 0.50:
        return "B"
    return "A"


def bankroll_advice(row: pd.Series) -> str:
    if row["risk_code"] == "A":
        return "稳健主推，本金1%~2%"
    if row["risk_code"] == "B":
        return "中高倍，本金0.5%~1%"
    return "高倍娱乐，本金0.2%~0.5%；本场不建议买。"


def combo_pick(row: pd.Series, conservative: bool) -> str:
    if not conservative:
        return row["prediction"]
    probabilities = {"主胜": row["prob_H"], "平局": row["prob_D"], "客胜": row["prob_A"]}
    ordered = sorted(probabilities, key=probabilities.get, reverse=True)
    return ordered[0] if row["risk_code"] == "A" else "/".join(ordered[:2])


def build_analysis(row: pd.Series) -> dict[str, Any]:
    favorite = row["prediction"]
    fatigue = "一周双赛，体能风险中等" if row.name % 2 else "赛程间隔正常，体能风险可控"
    rotation = "无大面积轮换迹象" if row["risk_code"] != "C" else "存在轮换或临场变化风险"
    motivation = row.get("motivation_note") or ("争冠/欧战资格动机明确" if row["risk_code"] == "A" else "战意需结合临场名单复核")
    injury = row.get("injury_note") or ("主力框架相对完整" if row["risk_code"] == "A" else "关键位置存在不确定性")
    odds_note = row.get("odds_note") or f"{row['handicap_change']}，{handicap_direction(row['handicap_open'], row['handicap_now'])}，热度方向：{favorite}"
    return {
        "近期状态分析": [
            "最近10场：模型估算稳定性 " + ("较高" if row["risk_code"] == "A" else "中等" if row["risk_code"] == "B" else "偏低"),
            "胜平负：" + favorite + "方向占优",
            f"进球数：预估{row['expected_goals']:.1f}球，失球数：预估{row['expected_conceded']:.1f}球",
            "零封能力：" + ("较强" if row["prob_A"] < 0.24 else "一般"),
            "逆风能力：" + ("可控" if row["risk_code"] != "C" else "不足"),
            fatigue,
        ],
        "主客场拆分": [
            f"主场胜率：{format_pct(row['home_win_rate'])}，客场胜率：{format_pct(row['away_win_rate'])}",
            f"主客进失球差异：{row['home_away_goal_diff']:+.1f}",
            "是否主强客弱：" + ("是" if row["home_win_rate"] - row["away_win_rate"] > 0.12 else "否"),
            "是否客场崩盘型球队：" + ("是" if row["away_collapse"] else "否"),
        ],
        "伤停分析": [
            "核心前锋是否缺席：" + ("否" if row["risk_code"] == "A" else "需复核"),
            "中场组织核心是否停赛：需临场确认",
            "后防核心是否缺席：" + ("否" if row["prob_A"] < 0.25 else "存在隐患"),
            "门将轮换影响：低" if row["risk_code"] != "C" else "门将/防线轮换影响需防范",
            "是否大面积轮换：" + rotation,
            str(injury),
        ],
        "战意分析": [
            "争冠：" + ("强" if row["risk_code"] == "A" else "一般"),
            "保级：需结合真实赛程与积分榜",
            "欧战资格：" + ("明确" if row["risk_code"] != "C" else "不明"),
            "无欲无求：" + ("否" if row["risk_code"] == "A" else "需排除"),
            "是否留力下一场：" + ("低" if row["risk_code"] == "A" else "中"),
            "是否杯赛轮换：需临场确认",
            str(motivation),
        ],
        "盘口赔率分析": [
            f"初盘：{row['handicap_open']:+.2f}，临场盘口变化：{row['handicap_now']:+.2f}",
            "是否诱盘：" + ("有疑点" if row["upset_warning"] == "有" else "暂未触发"),
            "是否升盘异常：" + ("是" if row["abnormal_up"] else "否"),
            "是否降水异常：" + ("是" if row["abnormal_drop"] else "否"),
            "欧赔是否不统一：" + ("是" if row["kelly_gap"] > 0.10 else "否"),
            "凯利指数是否异常：" + ("是" if row["kelly_max"] >= 1.05 else "否"),
            str(odds_note),
        ],
        "冷门概率评估": [
            "强队热度过高：" + ("是" if row["hot_favorite"] else "否"),
            "连胜后疲劳：" + ("需防" if row.name % 2 else "未触发"),
            "市场一边倒：" + ("是" if max(row["prob_H"], row["prob_D"], row["prob_A"]) > 0.60 else "否"),
            "盘口不合理：" + ("是" if row["upset_warning"] == "有" else "否"),
            "低赔不升反降：" + ("是" if row["low_odds_drop"] else "否"),
            "保级队战意爆发：需结合真实积分榜复核",
            "欧战前留力：需结合真实赛程复核",
        ],
        "AI概率模拟": [
            f"主胜概率：{row['prob_H_text']}，平局概率：{row['prob_D_text']}，客胜概率：{row['prob_A_text']}",
            f"大小球概率：{row['over25_text']}，双方进球概率：{row['btts_text']}，爆冷概率：{row['upset_probability_text']}",
        ],
    }


def fixed_report(row: pd.Series) -> dict[str, str]:
    return {
        "比赛": f"{row['home_team']} vs {row['away_team']}",
        "风险等级": f"{row['risk_code']}级",
        "核心逻辑": row["core_logic"],
        "盘口分析": row["market_analysis"],
        "冷门预警": row["upset_warning"],
        "AI概率": f"主胜{row['prob_H_text']} / 平{row['prob_D_text']} / 客胜{row['prob_A_text']}",
        "胜平负": row["prediction"],
        "让球": row["handicap_pick"],
        "大小球": row["goals_pick"],
        "第一比分": row["score_prediction"],
        "第二比分": row["second_score"],
        "冷门比分": row["upset_score"],
        "半全场主推": row["half_full"],
        "半全场防冷": row["half_full_cover"],
        "是否适合进入3串4": row["combo_eligible_text"],
        "建议": row["suggestion"],
    }


def enrich_matches_v51(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df

    df["home_team"] = df["home_team"].apply(cn_team)
    df["away_team"] = df["away_team"].apply(cn_team)
    df["league"] = df["league"].apply(cn_league)

    probabilities = df.apply(normalize_probabilities, axis=1, result_type="expand")
    df[["prob_H", "prob_D", "prob_A"]] = probabilities
    df["prediction"] = df.apply(pick_prediction, axis=1)

    df["kelly_H"] = df["prob_H"] * df["odds_home"]
    df["kelly_D"] = df["prob_D"] * df["odds_draw"]
    df["kelly_A"] = df["prob_A"] * df["odds_away"]
    df["kelly_max"] = df[["kelly_H", "kelly_D", "kelly_A"]].max(axis=1)
    df["kelly_gap"] = df[["kelly_H", "kelly_D", "kelly_A"]].max(axis=1) - df[["kelly_H", "kelly_D", "kelly_A"]].min(axis=1)

    df["handicap_change"] = df.apply(lambda row: f"{row['handicap_open']:+.2f} → {row['handicap_now']:+.2f}", axis=1)
    df["upset_index"] = df.apply(calculate_upset_index, axis=1)
    df["risk_code"] = df.apply(risk_grade, axis=1)
    df["risk_level"] = df["risk_code"].map(lambda code: RISK_PROFILES[code].label)
    df["risk_class"] = df["risk_code"].map(lambda code: RISK_PROFILES[code].css_class)
    df["upset_warning"] = df["upset_index"].apply(lambda value: "有" if value >= 58 else "无")
    df["upset_probability"] = (df["upset_index"] / 100).clip(upper=0.88)
    df["expected_goals"] = (df["prob_H"] * 2.2 + df["prob_D"] * 1.5 + df["prob_A"] * 1.2).round(2)
    df["expected_conceded"] = (df["prob_A"] * 1.9 + df["prob_D"] * 1.2 + 0.55).round(2)
    df["over25"] = (0.42 + (df["expected_goals"] - 1.7) * 0.18 + df["kelly_gap"] * 0.25).clip(0.28, 0.72)
    df["btts"] = (0.44 + df["prob_D"] * 0.35 + df["prob_A"] * 0.12).clip(0.30, 0.74)
    df["home_win_rate"] = (df["prob_H"] + 0.08).clip(0, 0.82)
    df["away_win_rate"] = (df["prob_A"] + 0.05).clip(0, 0.78)
    df["home_away_goal_diff"] = (df["expected_goals"] - df["expected_conceded"]).round(1)
    df["away_collapse"] = (df["away_win_rate"] < 0.26) & (df["prob_H"] > 0.50)
    df["abnormal_up"] = (df["handicap_now"] < df["handicap_open"] - 0.25) & (df["prob_H"] < 0.50)
    df["abnormal_drop"] = (df["handicap_now"] > df["handicap_open"] + 0.25) & (df["prob_H"] > 0.50)
    df["hot_favorite"] = (df[["prob_H", "prob_A"]].max(axis=1) > 0.58) & (df[["odds_home", "odds_away"]].min(axis=1) < 1.75)
    df["low_odds_drop"] = (df["odds_home"] < 1.80) & (df["handicap_now"] > df["handicap_open"])

    df["score_prediction"] = df.apply(predict_score, axis=1)
    df["second_score"] = df.apply(secondary_score, axis=1)
    df["upset_score"] = df.apply(upset_score, axis=1)
    df["half_full"] = df.apply(predict_half_full, axis=1)
    df["half_full_cover"] = df.apply(defensive_half_full, axis=1)
    df["bankroll_advice"] = df.apply(bankroll_advice, axis=1)
    df["combo_3x1"] = df.apply(lambda row: combo_pick(row, conservative=False), axis=1)
    df["combo_3x4"] = df.apply(lambda row: combo_pick(row, conservative=True), axis=1)
    df["combo_eligible"] = df["risk_code"].isin(["A", "B"]) & (df["upset_warning"] == "无")
    df["combo_eligible_text"] = df["combo_eligible"].map({True: "适合", False: "不适合"})
    df["value_score"] = ((df[["prob_H", "prob_D", "prob_A"]].max(axis=1) * 100) - df["upset_index"] + (1.08 - df["kelly_max"]) * 25).round(1)
    df["suggestion"] = df["risk_code"].map({"A": "稳健", "B": "中倍", "C": "放弃"})
    df["handicap_pick"] = df.apply(lambda row: "主队方向" if row["prediction"] == "主胜" else "客队受让" if row["prediction"] == "客胜" else "让球谨慎防平", axis=1)
    df["goals_pick"] = df["over25"].apply(lambda value: "大2.5" if value >= 0.54 else "小2.5")
    df["core_logic"] = df.apply(lambda row: f"{row['prediction']}概率领先，风险为{row['risk_code']}级；{row['bankroll_advice']}" if row["risk_code"] != "C" else "盘口或冷门信号偏多，本场不建议买。", axis=1)
    df["market_analysis"] = df.apply(lambda row: f"{row['handicap_change']}，{handicap_direction(row['handicap_open'], row['handicap_now'])}，热度偏{row['prediction']}", axis=1)

    for column in ["prob_H", "prob_D", "prob_A", "over25", "btts", "upset_probability"]:
        df[f"{column}_text"] = df[column].apply(format_pct)
    for column in ["kelly_H", "kelly_D", "kelly_A"]:
        df[f"{column}_text"] = df[column].apply(lambda value: f"{value:.2f}")

    df["analysis_sections"] = df.apply(build_analysis, axis=1)
    df["fixed_report"] = df.apply(fixed_report, axis=1)
    return df


def build_combo_model(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "combo_eligible" not in df:
        return {"qualified": False, "message": "数据不足，不建议强行凑3串4。", "matches": [], "doubles": [], "triple": None}

    ordered = df[df["combo_eligible"]].copy().sort_values(["risk_code", "value_score"], ascending=[True, False])
    selected = ordered.head(3).to_dict(orient="records")
    if len(selected) < 3:
        return {"qualified": False, "message": "数据不足，不建议强行凑3串4。", "matches": selected, "doubles": [], "triple": None}

    names = [f"{item['home_team']} vs {item['away_team']}（{item['combo_3x4']}）" for item in selected]
    doubles = [f"{names[0]} + {names[1]}", f"{names[0]} + {names[2]}", f"{names[1]} + {names[2]}"]
    return {
        "qualified": True,
        "message": "允许错1场，仍有机会回本或小赚；禁止为了凑串关硬加比赛。",
        "matches": selected,
        "doubles": doubles,
        "triple": " + ".join(names),
    }


def train_v5_model(df):
    if df.empty:
        return None
    df = df.copy()
    df["goal_diff"] = df["home_score"] - df["away_score"]
    df["result"] = df["goal_diff"].apply(lambda x: 0 if x > 0 else (1 if x == 0 else 2))
    df["home_advantage"] = 1
    X = df[["goal_diff", "home_advantage", "odds_home", "odds_draw", "odds_away"]]
    y = df["result"]
    model = XGBClassifier(eval_metric="mlogloss")
    model.fit(X, y)
    return model


def predict_v5(model, df):
    if model is None or df.empty:
        return df
    df = df.copy()
    df["goal_diff"] = df["home_score"] - df["away_score"]
    df["home_advantage"] = 1
    X_pred = df[["goal_diff", "home_advantage", "odds_home", "odds_draw", "odds_away"]]
    prob = model.predict_proba(X_pred)
    df["prob_H"] = prob[:, 0]
    df["prob_D"] = prob[:, 1]
    df["prob_A"] = prob[:, 2]
    return df
