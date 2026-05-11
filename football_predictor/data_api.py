from pathlib import Path
import json

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent

# 读取 config.json 中的 API_KEY
with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

API_KEY = config["API_KEY"]
BASE_URL = "https://api.football-data.org/v4/matches"


def fetch_matches():
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(BASE_URL, headers=headers, timeout=15)

    if response.status_code != 200:
        print("API请求失败：", response.status_code, response.text)
        return pd.DataFrame()

    data = response.json()

    matches = []
    for match in data.get("matches", []):
        matches.append(
            {
                "date": match.get("utcDate", ""),
                "league": match.get("competition", {}).get("name", ""),
                "home_team": match.get("homeTeam", {}).get("name", ""),
                "away_team": match.get("awayTeam", {}).get("name", ""),
                "home_score": (match.get("score", {}).get("fullTime", {}).get("home") or 0),
                "away_score": (match.get("score", {}).get("fullTime", {}).get("away") or 0),
                # 示例赔率，可以后续用真实 API 替换
                "odds_home": 2.0,
                "odds_draw": 3.2,
                "odds_away": 3.5,
            }
        )

    return pd.DataFrame(matches)
