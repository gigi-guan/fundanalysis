# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# plot1.py —— “收益-波动散点图（Plotly 版，可交互）”
#   1. 读取《产品分析_补全版.xlsx》
#   2. 清洗 5 个关键列
#   3. 返回 Plotly 散点图（颜色=夏普，大小=标准差）
# ------------------------------------------------------------
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px


# models/plot1.py
HERE = Path(__file__).resolve().parent.parent
EXCEL = HERE / "产品分析_补全版.xlsx"

FACTORS = {
    "年化收益2025": "最近一年（含2025年）的年化",
    "3年平均年化":  "过去3年平均年化",
    "标准差":      "基金标准差",
    "夏普比率":    "夏普比率",
    "最大回撤":    "最大回撤",
}

def _to_float(s):
    if isinstance(s, str):
        s = s.replace("%", "").replace(",", "").strip()
        return np.nan if s in ("", "-", "－") else float(s)
    return s

def _load_df() -> pd.DataFrame:
    # 如果文件不存在，就立刻抛错，方便排查
    if not EXCEL.exists():
        raise FileNotFoundError(f"找不到数据文件：{EXCEL}")
    # 全部先读成 str，更保险
    df = pd.read_excel(EXCEL, dtype=str)
    # 映射到新的五列
    for alias, col in FACTORS.items():
        if col not in df.columns:
            raise ValueError(f"缺失列：{col}，请检查 Excel 表头")
        df[alias] = df[col].apply(_to_float)
    # 至少要这几列都不为 NaN
    df = df.dropna(subset=list(FACTORS.keys()))
    return df

# ---------- 2. 公开给 Streamlit 调用 ----------
def build():
    """
    被 app.py 动态调用。返回 Plotly Figure。
    """
    df = _load_df()
    if df.empty:
        raise ValueError("清洗后无数据！")

    fig = px.scatter(
        df,
        x="年化收益2025",
        y="3年平均年化",
        color="夏普比率",
        size="标准差",
        hover_name="产品名称",         # 鼠标悬停显示
        color_continuous_scale="viridis",
        labels={
            "年化收益2025": "最近一年年化（%）",
            "3年平均年化": "过去3年平均年化（%）",
            "夏普比率": "夏普比率",
            "标准差": "标准差",
        },
        title="收益-波动散点图<br><sup>点色 = 夏普比率，点大小 = 标准差</sup>",
        height=600,
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="white")), opacity=0.8)
    fig.update_layout(coloraxis_colorbar=dict(title="夏普比率"))

    return fig   # ***** 关键：返回给 app.py *****

# ---------- 3. 让脚本可单独运行 ----------
if __name__ == "__main__":
    build().show()