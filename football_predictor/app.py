from flask import Flask, render_template

from data_api import CSV_FIELDS, load_matches
from models import RISK_PROFILES, build_combo_model

app = Flask(__name__)


def build_summary(df):
    if df.empty:
        return {
            "total_matches": 0,
            "a_risk": 0,
            "b_risk": 0,
            "c_risk": 0,
            "avg_upset": "0.0",
            "combo_count": 0,
            "top_pick": "-",
        }

    strongest_index = df[["prob_H", "prob_D", "prob_A"]].max(axis=1).idxmax()
    return {
        "total_matches": len(df),
        "a_risk": int((df["risk_code"] == "A").sum()),
        "b_risk": int((df["risk_code"] == "B").sum()),
        "c_risk": int((df["risk_code"] == "C").sum()),
        "avg_upset": f"{df['upset_index'].mean():.1f}",
        "combo_count": int(df["combo_eligible"].sum()),
        "top_pick": df.loc[strongest_index, "prediction"],
    }


@app.route("/")
def index():
    df, is_demo, data_source = load_matches()
    leagues = sorted(df["league"].dropna().unique()) if not df.empty else []
    summary = build_summary(df)
    combo_model = build_combo_model(df)
    return render_template(
        "index.html",
        data=df.to_dict(orient="records"),
        leagues=leagues,
        summary=summary,
        is_demo=is_demo,
        data_source=data_source,
        risk_profiles=RISK_PROFILES,
        combo_model=combo_model,
        csv_fields=CSV_FIELDS,
    )


if __name__ == "__main__":
    app.run(debug=True)
