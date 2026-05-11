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

系统按以下优先级加载数据：

1. **本地 CSV 优先**：如果 `football_predictor/matches.csv` 存在，系统会优先读取 CSV 数据，并在页面显示“当前使用 matches.csv 本地数据”。
2. **自动 API 赛程**：如果没有 CSV，系统会读取 `football_predictor/config.json` 中的 `API_KEY`，自动调用 football-data.org v4 `matches` 接口抓取今天和明天的比赛，并在页面显示“当前使用 API 自动抓取赛程”。
3. **演示数据兜底**：如果 `API_KEY` 未配置、接口失败或没有返回比赛，系统会使用内置示例比赛，保证网站可直接启动和预览，并提示“当前为演示数据，请导入 matches.csv 或配置 API_KEY 获取真实赛程”。

### 配置 football-data.org API_KEY

1. 访问 <https://www.football-data.org/> 注册并申请 API Key。
2. 打开 `football_predictor/config.json`。
3. 将申请到的 Key 填入 `API_KEY` 字段：

```json
{
  "API_KEY": "你的 football-data.org API Key"
}
```

> `config.json` 默认保留为空字符串，避免提交个人密钥。

### 使用 matches.csv

将 `matches.csv` 放到 `football_predictor/` 目录即可覆盖 API 和演示数据。CSV 可使用中文列名（如 `日期`、`联盟`、`概率H`、`客场_球队`）或英文列名（如 `date`、`league`、`prob_H`、`away_team`），应用会做兼容映射。

建议 CSV 尽量补充以下字段，以便 V5.1 模型完整分析：

- 赛程基础：`date`、`time`、`league`、`home_team`、`away_team`
- 胜平负概率：`home_prob`、`draw_prob`、`away_prob`
- 盘口：`handicap_open`、`handicap_live`
- 凯利：`kelly_home`、`kelly_draw`、`kelly_away`
- 人工分析：`injury_note`、`motivation_note`、`odds_note`

### API 数据与 CSV 数据的区别

football-data.org 的 `matches` 接口主要返回赛程、联赛、球队、开球时间、比分状态等基础信息。它通常不提供盘口、欧赔、凯利指数、伤停、战意、赔率说明等赛前交易和情报字段。

因此，当系统使用 API 自动抓取赛程时，盘口、凯利、伤停、战意、赔率等缺失项会显示：

- `数据不足`
- `本场不建议买`
- `需要补充盘口/伤停/赔率数据后再分析`

如需完整使用盘口赔率分析、3串4筛选和风险控制模型，请优先导入包含完整字段的 `matches.csv`。

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
