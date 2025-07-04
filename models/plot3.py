#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot3.py —— 3-D 皮尔逊相关系数曲面图（matplotlib）
build(df) → matplotlib Figure
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
import matplotlib.font_manager as fm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

COLS_RAW = [
    "最近一年（含2025年）的年化", "过去3年平均年化", "过去3年累计回报",
    "2024年年化","2023年年化","2022年年化","2021年年化","2020年年化",
    "基金标准差", "投资组合预期年化报酬率",
    "年化无风险利率（平均回报减去预期年化的绝对值）",
    "夏普比率","最大回撤","卡玛比率",
]

ALIAS_MAP = {
    "最近一年（含2025年）的年化": "近1Y年化",
    "过去3年平均年化": "3Y平均年化",
    "过去3年累计回报": "3Y累计回报",
    "投资组合预期年化报酬率": "组合预期年化",
    "年化无风险利率（平均回报减去预期年化的绝对值）": "无风险年化",
}

def init_chinese_font() -> str:
    cand = ["PingFang SC","Heiti TC","Microsoft YaHei","SimHei"]
    installed = [f.name for f in fm.fontManager.ttflist]
    name = next((c for c in cand if c in installed), "SimHei")
    plt.rcParams["font.family"] = name
    plt.rcParams["axes.unicode_minus"] = False
    return name

def _clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    missing = [c for c in COLS_RAW if c not in df.columns]
    if missing:
        raise ValueError(f"plot3.py 缺列：{missing}")
    df2 = df.rename(columns=ALIAS_MAP)
    cols = [ALIAS_MAP.get(c, c) for c in COLS_RAW]
    for c in cols:
        df2[c] = (
            df2[c].astype(str)
                 .str.replace("%","").str.replace(",","")
                 .replace({"-":np.nan,"":np.nan})
                 .astype(float)
        )
    df2 = df2.dropna(subset=cols)
    return df2, cols

def build_figure(df: pd.DataFrame, cols: list[str]):
    corr = df[cols].corr()
    n = len(cols)
    X, Y = np.meshgrid(range(n), range(n))
    Z = corr.values

    norm = Normalize(vmin=-1, vmax=1)
    colors = cm.coolwarm(norm(Z))

    fig = plt.figure(figsize=(13, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(
        X, Y, Z, facecolors=colors,
        rstride=1, cstride=1, linewidth=0,
        antialiased=False, shade=False
    )
    ax.set_zlim(-1, 1)
    ax.set_zlabel("相关系数")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(cols, rotation=60, ha="right")
    ax.set_yticklabels(cols)

    mappable = cm.ScalarMappable(norm=norm, cmap="coolwarm")
    mappable.set_array([])
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.65, pad=0.08)
    cbar.ax.set_ylabel("相关系数")

    fig.suptitle("各因子皮尔逊相关系数 — 3D 立体热力图", fontsize=16, y=0.94)
    fig.tight_layout()
    return fig

def build(df: pd.DataFrame):
    """
    供 app.py 调用，返回 matplotlib Figure
    """
    init_chinese_font()
    df2, cols = _clean(df)
    if df2.empty:
        raise ValueError("plot3.py：无有效数据")
    return build_figure(df2, cols)

# 单独调试保持原有逻辑
if __name__ == "__main__":
    import datetime as dt
    from pathlib import Path
    EXCEL_FILE = Path("/Users/gigiguan/Downloads/产品分析_补全版.xlsx")
    df_raw = pd.read_excel(EXCEL_FILE, dtype=str)
    df2, _ = _clean(df_raw)
    fig = build(df2)
    out = EXCEL_FILE.with_name(f"heatmap3d_{dt.datetime.now():%Y%m%d_%H%M%S}.png")
    fig.savefig(out, dpi=300)
    print("✅ 已保存到", out)
    plt.show()