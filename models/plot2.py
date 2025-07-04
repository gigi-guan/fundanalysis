# -*- coding: utf-8 -*-
# plot2.py —— “因子相关系数热力图”
#   被 Streamlit 调用：from plot2 import build; fig = build()
#   单独运行：python plot2.py          -> 会弹窗口并保存 PNG

import datetime as dt
from pathlib import Path
import sys, numpy as np, pandas as pd, seaborn as sns

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pyplotz.pyplotz import PyplotZ

# ------------ 0. 列配置 & 中文字体 ----------------
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

def _init_chinese_font() -> str:
    cand = ["PingFang SC","Microsoft YaHei","Source Han Sans CN","SimHei"]
    installed = matplotlib.font_manager.get_font_names()
    name = next((f for f in cand if f in installed), "SimHei")
    plt.rcParams["font.family"] = name
    plt.rcParams["axes.unicode_minus"] = False
    return name

CH_FONT = _init_chinese_font()
CH_PROP = fm.FontProperties(family=CH_FONT)

# ------------ 1. 数据读取 & 清洗 ------------------
EXCEL = Path("/Users/gigiguan/Downloads/产品分析_补全版.xlsx")   # ←← 修改路径

def _load_and_clean() -> tuple[pd.DataFrame, list[str]]:
    if not EXCEL.exists():
        sys.exit(f"❌ 找不到文件：{EXCEL}")
    df = pd.read_excel(EXCEL, dtype=str)

    miss = [c for c in COLS_RAW if c not in df.columns]
    if miss:
        sys.exit(f"❌ Excel 缺列：{miss}")

    df = df.rename(columns=ALIAS_MAP)
    cols = [ALIAS_MAP.get(c, c) for c in COLS_RAW]

    def _to_num(s: str) -> float|None:
        if isinstance(s, str):
            s = s.replace("%","").replace(",","").strip()
            return np.nan if s in ("","-","－") else float(s)
        return s

    for c in cols:
        df[c] = df[c].apply(_to_num)
    df = df.dropna(subset=cols)
    return df, cols

# ------------ 2. 画图函数 -------------------------
def _draw(df: pd.DataFrame, cols: list[str]):
    corr = df[cols].corr("pearson")
    mask = np.zeros_like(corr, dtype=bool)  # 全显示

    pltz = PyplotZ(); fig, ax = plt.subplots(figsize=(14,12))
    sns.set_style("white")
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f",
        cmap="coolwarm", center=0, square=True, linewidths=.5,
        cbar_kws={"shrink": .8, "label": "相关系数"},
        annot_kws={"fontsize":9, "fontproperties":CH_PROP},
        ax=ax,
    )
    ax.set_xticklabels(ax.get_xticklabels(), rotation=60, ha="right",
                       fontproperties=CH_PROP, fontsize=9)
    ax.set_yticklabels(ax.get_yticklabels(),
                       fontproperties=CH_PROP, fontsize=9)
    ax.collections[0].colorbar.ax.yaxis.label.set_fontproperties(CH_PROP)
    for t in ax.collections[0].colorbar.ax.get_yticklabels():
        t.set_fontproperties(CH_PROP)

    pltz.title("各因子皮尔逊相关系数矩阵", fontsize=18)
    plt.tight_layout()
    return fig

# ------------ 3. 供 Streamlit 调用 ----------------
def build():
    """返回 plotly/mpl figure，供 app.py 调用"""
    df, cols = _load_and_clean()
    if df.empty:
        raise ValueError("清洗后无有效数据")
    return _draw(df, cols)

# ------------ 4. 单独运行时 -----------------------
if __name__ == "__main__":
    fig = build()
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = EXCEL.with_name(f"heatmap_corr_{ts}.png")
    fig.savefig(out, dpi=300)
    print(f"✅ 已保存 {out}")
    plt.show()