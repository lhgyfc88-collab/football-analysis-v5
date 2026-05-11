# football-analysis-v5

足球量化分析网站，基于 Python / Flask / Pandas 构建。当前版本升级为“足球量化赛前分析专业版 V5.0”，提供赛前比赛看板、胜平负概率、比分预测、半全场、冷门指数、盘口变化、凯利指数、风险等级、资金管理建议，以及 3串1 / 3串4 容错结构。

## 项目结构

```text
football_predictor/
├── app.py                    # Flask 入口与赛前分析指标计算
├── data_api.py               # football-data.org 比赛接口读取工具
├── models.py                 # 保留的 XGBoost 训练与预测逻辑
├── config.json               # API 配置
├── requirements.txt          # Python 依赖
├── static/css/style.css      # 专业版页面样式
└── templates/index.html      # 页面模板与前端筛选 / 图表逻辑
```

## 本地运行

```bash
cd football_predictor
python -m venv .venv
source .venv/bin/activate  # Windows 可使用 .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

启动后访问：<http://127.0.0.1:5000>

## 数据说明

- 如果 `football_predictor/matches.csv` 存在，系统会优先读取 CSV 数据。
- 如果没有 CSV，系统会使用内置示例比赛，保证网站可直接启动和预览。
- CSV 可使用中文列名（如 `日期`、`联盟`、`概率H`、`客场_球队`）或英文列名（如 `date`、`league`、`prob_H`、`away_team`），应用会做兼容映射。

## 专业分析模块

- 今日比赛列表
- 胜平负概率
- 比分预测
- 半全场预测
- 冷门指数
- 风险等级
- 盘口变化
- 凯利指数
- 资金管理建议
- 3串1、3串4 容错结构
