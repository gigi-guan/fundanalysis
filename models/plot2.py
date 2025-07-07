# -*- coding: utf-8 -*-
# plot2.py —— 交互式“因子相关系数热力图” (Plotly 版)

import pandas as pd
import numpy as np
import plotly.express as px

# 原来的列配置 & 别名映射
COLS_RAW = [
    "最近一年（含2025年）的年化", "过去3年平均年化", "过去3年累计回报",
    "2024年年化","2023年年化","2022年年化","2021年年化","2020年年化",
    "基金标准差", "投资组合预期年化报酬率",
    "年化无风险利率（平均回报减去预期年化的绝对值）",
    "夏普比率","最大回撤","卡玛比率"
]
ALIAS_MAP = {
    "最近一年（含2025年）的年化": "近1Y年化",
    "过去3年平均年化":       "3Y平均年化",
    "过去3年累计回报":       "3Y累计回报",
    "投资组合预期年化报酬率": "组合预期年化",
    "年化无风险利率（平均回报减去预期年化的绝对值）": "无风险年化",
}

EXCEL = "产品分析_补全版.xlsx"
df_all = pd.read_excel(EXCEL)

def _load_and_clean():
    if not EXCEL.exists():
        raise FileNotFoundError(f"❌ 找不到文件：{EXCEL}")
    df = pd.read_excel(EXCEL, dtype=str)
    # 检查缺列
    miss = [c for c in COLS_RAW if c not in df.columns]
    if miss:
        raise KeyError(f"❌ Excel 缺列：{miss}")
    # 重命名
    df = df.rename(columns=ALIAS_MAP)
    cols = [ALIAS_MAP.get(c, c) for c in COLS_RAW]
    # 转数值
    def to_num(s):
        if isinstance(s, str):
            v = s.replace("%","").replace(",","").strip()
            return np.nan if v in ("","-","－") else float(v)
        return s
    for c in cols:
        df[c] = df[c].map(to_num)
    df = df.dropna(subset=cols)
    return df, cols

def build():
    """
    返回一个 Plotly Figure，供 app.py 用 st.plotly_chart 显示。
    """
    df, cols = _load_and_clean()
    corr = df[cols].corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        origin="lower",
        labels={"x":"因子","y":"因子","color":"相关系数"},
        title="各因子皮尔逊相关系数矩阵"
    )
    fig.update_xaxes(tickangle=60)
    fig.update_layout(font_family="Microsoft YaHei")
    return fig