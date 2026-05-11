from flask import Flask, render_template
import pandas as pd
import json

app = Flask(__name__)

# 从 config.json 或 data_api.py 得到数据
df = pd.read_csv("matches.csv")  # 你的比赛数据 CSV

# 增加计算列
df['prob_H'] = df['概率H']
df['prob_D'] = df['概率D']
df['prob_A'] = df['概率A']
df['target_diff'] = df['目标差异']
df['home_adv'] = df['主场优势']

leagues = sorted(df['联盟'].unique())

@app.route("/")
def index():
    return render_template("index.html", data=df.to_dict(orient='records'), leagues=leagues)

if __name__ == "__main__":
    app.run(debug=True)