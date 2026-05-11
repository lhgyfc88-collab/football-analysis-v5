from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Any

import pandas as pd
import requests

from models import cn_league, cn_team, enrich_matches_v51

BASE_DIR = Path(__file__).resolve().parent
MATCHES_CSV = BASE_DIR / "matches.csv"
CONFIG_PATH = BASE_DIR / "config.json"
BASE_URL = "https://api.football-data.org/v4/matches"

COLUMN_ALIASES = {
    "日期": "date",
    "时间": "time",
    "联盟": "league",
    "联赛": "league",
    "主队": "home_team",
    "主场_球队": "home_team",
    "客队": "away_team",
    "客场_球队": "away_team",
    "主胜概率": "home_prob",
    "平局概率": "draw_prob",
    "客胜概率": "away_prob",
    "概率H": "prob_H",
    "概率D": "prob_D",
    "概率A": "prob_A",
    "初盘": "handicap_open",
    "临场盘口": "handicap_live",
    "即时盘口": "handicap_live",
    "伤停": "injury_note",
    "战意": "motivation_note",
    "赔率说明": "odds_note",
}

REQUIRED_DEFAULTS: dict[str, Any] = {
    "date": "待定",
    "time": "",
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
    "handicap_live": 0.0,
    "kelly_home": None,
    "kelly_draw": None,
    "kelly_away": None,
    "injury_note": "",
    "motivation_note": "",
    "odds_note": "",
    "data_source": "csv",
    "data_quality": "complete",
}

NUMERIC_COLUMNS = [
    "home_score",
    "away_score",
    "odds_home",
    "odds_draw",
    "odds_away",
    "opening_home",
    "opening_draw",
    "opening_away",
    "handicap_open",
    "handicap_live",
    "handicap_now",
    "home_prob",
    "draw_prob",
    "away_prob",
    "prob_H",
    "prob_D",
    "prob_A",
    "kelly_home",
    "kelly_draw",
    "kelly_away",
]

CSV_FIELDS = [
    "date",
    "time",
    "league",
    "home_team",
    "away_team",
    "home_prob",
    "draw_prob",
    "away_prob",
    "handicap_open",
    "handicap_live",
    "kelly_home",
    "kelly_draw",
    "kelly_away",
    "injury_note",
    "motivation_note",
    "odds_note",
]


def demo_matches() -> pd.DataFrame:
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    rows = [
        {
            "date": today.isoformat(),
            "time": "19:30",
            "league": "英超",
            "home_team": "曼城",
            "away_team": "切尔西",
            "odds_home": 1.72,
            "odds_draw": 3.85,
            "odds_away": 4.80,
            "opening_home": 1.80,
            "opening_draw": 3.70,
            "opening_away": 4.50,
            "handicap_open": -0.75,
            "handicap_live": -1.00,
            "home_score": 2,
            "away_score": 1,
            "motivation_note": "争冠与欧战席位动机明确，热度需控制。",
        },
        {
            "date": today.isoformat(),
            "time": "20:00",
            "league": "西甲",
            "home_team": "皇家马德里",
            "away_team": "比利亚雷亚尔",
            "odds_home": 1.58,
            "odds_draw": 4.10,
            "odds_away": 5.60,
            "opening_home": 1.64,
            "opening_draw": 4.00,
            "opening_away": 5.20,
            "handicap_open": -1.00,
            "handicap_live": -1.25,
            "home_score": 2,
            "away_score": 0,
            "injury_note": "主力框架相对完整，但需赛前确认轮换。",
        },
        {
            "date": today.isoformat(),
            "time": "20:45",
            "league": "意甲",
            "home_team": "国际米兰",
            "away_team": "罗马",
            "odds_home": 2.05,
            "odds_draw": 3.35,
            "odds_away": 3.65,
            "opening_home": 2.15,
            "opening_draw": 3.25,
            "opening_away": 3.45,
            "handicap_open": -0.25,
            "handicap_live": -0.50,
            "home_score": 1,
            "away_score": 1,
            "odds_note": "主队方向升盘，平局保护不可忽略。",
        },
        {
            "date": tomorrow.isoformat(),
            "time": "21:00",
            "league": "德甲",
            "home_team": "多特蒙德",
            "away_team": "勒沃库森",
            "odds_home": 2.70,
            "odds_draw": 3.55,
            "odds_away": 2.46,
            "opening_home": 2.55,
            "opening_draw": 3.50,
            "opening_away": 2.60,
            "handicap_open": 0.00,
            "handicap_live": 0.25,
            "home_score": 1,
            "away_score": 2,
            "motivation_note": "强强对话分歧较大，适合作为观察或容错位。",
        },
        {
            "date": tomorrow.isoformat(),
            "time": "22:00",
            "league": "法甲",
            "home_team": "巴黎圣日耳曼",
            "away_team": "里昂",
            "odds_home": 1.68,
            "odds_draw": 3.95,
            "odds_away": 4.90,
            "opening_home": 1.75,
            "opening_draw": 3.75,
            "opening_away": 4.65,
            "handicap_open": -0.75,
            "handicap_live": -1.00,
            "home_score": 3,
            "away_score": 1,
            "injury_note": "进攻端优势明显，防线仍需关注临场名单。",
        },
    ]
    return pd.DataFrame(rows)


def prepare_matches(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={key: value for key, value in COLUMN_ALIASES.items() if key in df.columns}).copy()

    for column, default in REQUIRED_DEFAULTS.items():
        if column not in df.columns:
            df[column] = default

    if "handicap_now" not in df.columns:
        df["handicap_now"] = df["handicap_live"]
    else:
        df["handicap_now"] = df["handicap_now"].fillna(df["handicap_live"])

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["opening_home"] = df["opening_home"].fillna(df["odds_home"])
    df["opening_draw"] = df["opening_draw"].fillna(df["odds_draw"])
    df["opening_away"] = df["opening_away"].fillna(df["odds_away"])
    df["handicap_now"] = df["handicap_now"].fillna(df["handicap_live"]).fillna(0.0)
    df["handicap_open"] = df["handicap_open"].fillna(0.0)
    df["date"] = df["date"].astype(str)
    df["time"] = df["time"].fillna("").astype(str)
    df["league"] = df["league"].apply(cn_league)
    df["home_team"] = df["home_team"].apply(cn_team)
    df["away_team"] = df["away_team"].apply(cn_team)
    df["match_time"] = df.apply(lambda row: f"{row['date']} {row['time']}".strip(), axis=1)
    return enrich_matches_v51(df)


def apply_api_limitations(df: pd.DataFrame) -> pd.DataFrame:
    """Mark football-data.org fixtures as schedule-only rows that require manual market data."""
    if df.empty:
        return df

    df = df.copy()
    api_mask = df.get("data_quality", pd.Series(index=df.index, dtype="object")).eq("api_basic")
    if not api_mask.any():
        return df

    insufficient = "数据不足"
    no_buy = "本场不建议买"
    supplement = "需要补充盘口/伤停/赔率数据后再分析"
    api_sections = {
        "近期状态分析": [insufficient, no_buy, supplement],
        "主客场拆分": [insufficient, no_buy, supplement],
        "伤停分析": [insufficient, no_buy, supplement],
        "战意分析": [insufficient, no_buy, supplement],
        "盘口赔率分析": [insufficient, no_buy, supplement],
        "冷门概率评估": [insufficient, no_buy, supplement],
        "AI概率模拟": [insufficient, no_buy, supplement],
    }

    for index in df[api_mask].index:
        match_name = f"{df.at[index, 'home_team']} vs {df.at[index, 'away_team']}"
        df.at[index, "risk_code"] = "C"
        df.at[index, "risk_level"] = "C级：高风险"
        df.at[index, "risk_class"] = "risk-c"
        df.at[index, "prediction"] = insufficient
        df.at[index, "bankroll_advice"] = no_buy
        df.at[index, "score_prediction"] = insufficient
        df.at[index, "second_score"] = insufficient
        df.at[index, "upset_score"] = insufficient
        df.at[index, "half_full"] = insufficient
        df.at[index, "half_full_cover"] = insufficient
        df.at[index, "combo_3x1"] = insufficient
        df.at[index, "combo_3x4"] = insufficient
        df.at[index, "combo_eligible"] = False
        df.at[index, "combo_eligible_text"] = "不适合"
        df.at[index, "suggestion"] = "放弃"
        df.at[index, "handicap_pick"] = insufficient
        df.at[index, "goals_pick"] = insufficient
        df.at[index, "core_logic"] = supplement
        df.at[index, "market_analysis"] = supplement
        df.at[index, "handicap_change"] = insufficient
        df.at[index, "kelly_H_text"] = insufficient
        df.at[index, "kelly_D_text"] = insufficient
        df.at[index, "kelly_A_text"] = insufficient
        df.at[index, "over25_text"] = insufficient
        df.at[index, "btts_text"] = insufficient
        df.at[index, "upset_warning"] = "有"
        df.at[index, "analysis_sections"] = api_sections
        df.at[index, "fixed_report"] = {
            "比赛": match_name,
            "风险等级": "C级",
            "核心逻辑": supplement,
            "盘口分析": supplement,
            "冷门预警": insufficient,
            "AI概率": insufficient,
            "胜平负": insufficient,
            "让球": insufficient,
            "大小球": insufficient,
            "第一比分": insufficient,
            "第二比分": insufficient,
            "冷门比分": insufficient,
            "半全场主推": insufficient,
            "半全场防冷": insufficient,
            "是否适合进入3串4": "不适合",
            "建议": no_buy,
        }
    return df


def load_matches() -> tuple[pd.DataFrame, bool, str]:
    """Load CSV first, then API fixtures, and finally demo data as a safe fallback."""
    if MATCHES_CSV.exists():
        df = pd.read_csv(MATCHES_CSV)
        df["data_source"] = "csv"
        df["data_quality"] = "complete"
        return prepare_matches(df), False, "csv"

    api_df = fetch_matches()
    if not api_df.empty:
        return api_df, False, "api"

    df = demo_matches()
    df["data_source"] = "demo"
    df["data_quality"] = "complete"
    return prepare_matches(df), True, "demo"


def read_api_key() -> str:
    """Read football-data.org API key from config.json without crashing the web page."""
    if not CONFIG_PATH.exists():
        return ""

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print("配置读取失败：", exc)
        return ""
    return str(config.get("API_KEY") or "").strip()


def fetch_matches() -> pd.DataFrame:
    """Fetch today/tomorrow fixtures from football-data.org v4 matches API."""
    api_key = read_api_key()
    if not api_key:
        return pd.DataFrame()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    params = {"dateFrom": today.isoformat(), "dateTo": tomorrow.isoformat()}

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            headers={"X-Auth-Token": api_key},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        print("API请求失败：", exc)
        return pd.DataFrame()
    except ValueError as exc:
        print("API响应解析失败：", exc)
        return pd.DataFrame()

    matches = []
    for match in payload.get("matches", []):
        utc_date = match.get("utcDate", "") or ""
        score = match.get("score", {}).get("fullTime", {}) or {}
        matches.append(
            {
                "date": utc_date[:10],
                "time": utc_date[11:16],
                "league": match.get("competition", {}).get("name", ""),
                "home_team": match.get("homeTeam", {}).get("name", ""),
                "away_team": match.get("awayTeam", {}).get("name", ""),
                "home_score": score.get("home") or 0,
                "away_score": score.get("away") or 0,
                "data_source": "api",
                "data_quality": "api_basic",
                "injury_note": "数据不足",
                "motivation_note": "数据不足",
                "odds_note": "需要补充盘口/伤停/赔率数据后再分析",
            }
        )

    if not matches:
        return pd.DataFrame()
    return apply_api_limitations(prepare_matches(pd.DataFrame(matches)))
