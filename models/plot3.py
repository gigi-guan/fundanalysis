# -*- coding: utf-8 -*-
# models/plot3.py —— 交互式 3D 皮尔逊相关系数曲面图（Plotly 版）

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# 原来的列配置 & 别名映射
COLS_RAW = [
    "最近一年（含2025年）的年化", "过去3年平均年化", "过去3年累计回报",
    "2024年年化","2023年年化","2022年年化","2021年年化","2020年年化",
    "基金标准差", "投资组合预期年化报酬率",
    "年化无风险利率（平均回报减去预期年化的绝对值）",
    "夏普比率","最大回撤","卡玛比率",
]
ALIAS_MAP = {
    "最近一年（含2025年）的年化": "近1Y年化",
    "过去3年平均年化":       "3Y平均年化",
    "过去3年累计回报":       "3Y累计回报",
    "投资组合预期年化报酬率": "组合预期年化",
    "年化无风险利率（平均回报减去预期年化的绝对值）": "无风险年化",
}

HERE = Path(__file__).resolve().parent.parent
EXCEL = HERE / "产品分析_补全版.xlsx"

def _clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    # 检查列
    missing = [c for c in COLS_RAW if c not in df.columns]
    if missing:
        raise ValueError(f"plot3.py 缺列：{missing}")
    # 重命名
    df2 = df.rename(columns=ALIAS_MAP)
    cols = [ALIAS_MAP.get(c, c) for c in COLS_RAW]
    # 转 float
    def to_num(s):
        if isinstance(s, str):
            v = s.replace("%", "").replace(",", "").strip()
            return np.nan if v in ("", "-", "－") else float(v)
        return s
    for c in cols:
        df2[c] = df2[c].map(to_num)
    df2 = df2.dropna(subset=cols)
    return df2, cols

def build() -> go.Figure:
    """
    供 app.py 调用，返回一个 Plotly Figure
    """
    # 1. 读表
    df_raw = pd.read_excel(EXCEL, dtype=str)
    # 2. 清洗
    df2, cols = _clean(df_raw)
    if df2.empty:
        raise ValueError("plot3.py：无有效数据")
    # 3. 计算相关系数矩阵
    corr = df2[cols].corr().values
    n = len(cols)
    # 4. 绘 surface
    fig = go.Figure(
        data=go.Surface(
            z=corr,
            x=list(range(n)),
            y=list(range(n)),
            surfacecolor=corr,
            colorscale='RdBu',
            cmin=-1, cmax=1,
            colorbar=dict(title="相关系数")
        )
    )
    # 5. 坐标轴、布局
    fig.update_layout(
        title="各因子皮尔逊相关系数 — 3D 立体热力图",
        scene=dict(
            xaxis=dict(
                title="因子",
                tickmode="array",
                tickvals=list(range(n)),
                ticktext=cols
            ),
            yaxis=dict(
                title="因子",
                tickmode="array",
                tickvals=list(range(n)),
                ticktext=cols
            ),
            zaxis=dict(title="相关系数", range=[-1, 1])
        ),
        font_family="Microsoft YaHei",
        margin=dict(l=0, r=0, t=50, b=0)
    )
    return fig

# 允许单独调试
if __name__ == "__main__":
    fig = build()
    fig.write_html("plot3_surface.html")
    print("✅ 已输出为 plot3_surface.html")