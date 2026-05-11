import pandas as pd
from xgboost import XGBClassifier

def train_v5_model(df):
    if df.empty:
        return None

    df = df.copy()
    df["goal_diff"] = df["home_score"] - df["away_score"]
    # 0=主胜, 1=平, 2=客胜
    df["result"] = df["goal_diff"].apply(lambda x: 0 if x > 0 else (1 if x == 0 else 2))
    df["home_advantage"] = 1

    X = df[["goal_diff", "home_advantage", "odds_home", "odds_draw", "odds_away"]]
    y = df["result"]

    model = XGBClassifier(use_label_encoder=False, eval_metric="mlogloss")
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

    # 半全场预测示例
    df["half_full"] = df["prob_H"] * 0.6 + df["prob_D"] * 0.3

    # 常见比分概率示例
    df["score_1_0"] = df["prob_H"] * 0.4
    df["score_2_1"] = df["prob_H"] * 0.3
    df["score_1_1"] = df["prob_D"] * 0.5

    # 总进球预测
    df["total_goals"] = df["home_score"] + df["away_score"]
    df["goal_over_2_5"] = (df["total_goals"] > 2.5).astype(int)

    return df