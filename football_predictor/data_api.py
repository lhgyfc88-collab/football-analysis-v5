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


def load_matches() -> tuple[pd.DataFrame, bool]:
    """Load user CSV data when present; otherwise generate today/tomorrow demo fixtures."""
    if MATCHES_CSV.exists():
        df = pd.read_csv(MATCHES_CSV)
        return prepare_matches(df), False
    return prepare_matches(demo_matches()), True


def fetch_matches() -> pd.DataFrame:
    """Fetch public API matches when an API key exists; returned data is normalized to Chinese labels."""
    if not CONFIG_PATH.exists():
        return pd.DataFrame()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    api_key = config.get("API_KEY")
    if not api_key:
        return pd.DataFrame()

    response = requests.get(BASE_URL, headers={"X-Auth-Token": api_key}, timeout=15)
    if response.status_code != 200:
        print("API请求失败：", response.status_code, response.text)
        return pd.DataFrame()

    matches = []
    for match in response.json().get("matches", []):
        matches.append(
            {
                "date": match.get("utcDate", "")[:10],
                "time": match.get("utcDate", "")[11:16],
                "league": cn_league(match.get("competition", {}).get("name", "")),
                "home_team": cn_team(match.get("homeTeam", {}).get("name", "")),
                "away_team": cn_team(match.get("awayTeam", {}).get("name", "")),
                "home_score": (match.get("score", {}).get("fullTime", {}).get("home") or 0),
                "away_score": (match.get("score", {}).get("fullTime", {}).get("away") or 0),
                "odds_home": 2.0,
                "odds_draw": 3.2,
                "odds_away": 3.5,
            }
        )
    return prepare_matches(pd.DataFrame(matches)) if matches else pd.DataFrame()
