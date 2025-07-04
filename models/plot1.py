# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# plot1.py —— “收益-波动散点图”
#   1. 读取《产品分析_补全版.xlsx》
#   2. 清洗 5 个关键列
#   3. 画散点（颜色=夏普，大小=标准差）
#   4. Hover 显示“产品名称”（中文正常）
# ------------------------------------------------------------
import os, sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import mplcursors
from pyplotz.pyplotz import PyplotZ

# ---------- 0. 选定并写入全局中文字体 ----------
def init_chinese_font() -> str:
    """挑一个系统已安装的中文字体并写入 rcParams，返回字体名"""
    cand = [
        "PingFang SC",           # macOS
        "Microsoft YaHei",       # Windows
        "Source Han Sans CN",    # Adobe / Linux
        "WenQuanYi Zen Hei",     # Linux
        "SimHei", "STHeiti", "Heiti SC", "Hiragino Sans GB"
    ]
    installed = {f.name for f in fm.fontManager.ttflist}
    name = next((f for f in cand if f in installed), "SimHei")

    matplotlib.rcParams["font.sans-serif"] = [name]
    matplotlib.rcParams["axes.unicode_minus"] = False
    return name


CH_FONT = init_chinese_font()          # 写 rcParams
CH_PROP = fm.FontProperties(family=CH_FONT)

# pyplotz 也用同一字体（它不会接收 font 参数，直接启用即可）
pltz = PyplotZ()
pltz.enable_chinese()

# ---------- 1. 读数据 ----------
EXCEL = "/Users/gigiguan/Downloads/产品分析_补全版.xlsx"
if not os.path.exists(EXCEL):
    sys.exit(f"❌ 找不到文件：{EXCEL}")
df = pd.read_excel(EXCEL, dtype=str)

# ---------- 2. 清洗 ----------
FACTORS = {
    "年化收益2025": "最近一年（含2025年）的年化",
    "3年平均年化":  "过去3年平均年化",
    "标准差":      "基金标准差",
    "夏普比率":    "夏普比率",
    "最大回撤":    "最大回撤",
}

def _to_float(s: str) -> float:
    if isinstance(s, str):
        s = s.replace("%", "").replace(",", "").strip()
        return np.nan if s in ("", "-", "－") else float(s)
    return s

for alias, col in FACTORS.items():
    df[alias] = df[col].apply(_to_float)

df = df.dropna(subset=list(FACTORS.keys()))
if df.empty:
    sys.exit("❌ 清洗后无数据！")

# ---------- 3. 绘图 ----------
plt.figure(figsize=(10, 8))
sns.set_style("whitegrid", {"grid.linestyle": "--"})

sc = plt.scatter(
    x=df["年化收益2025"],
    y=df["3年平均年化"],
    c=df["夏普比率"],
    s=df["标准差"] * 20,      # 点大小 ∝ 波动率
    cmap="viridis",
    alpha=0.75,
    edgecolors="white",
    linewidths=0.5,
)

# colorbar
cbar = plt.colorbar(sc)
cbar.set_label("夏普比率", fontproperties=CH_PROP, fontsize=12)

# 标题 / 轴标签
pltz.title("最近一年年化 vs 过去3年平均年化\n（点色 = 夏普比率，点大小 = 标准差）", fontsize=16)
pltz.xlabel("最近一年年化（%）", fontsize=14)
pltz.ylabel("过去3年平均年化（%）", fontsize=14)

# ---------- 4. Hover：mplcursors 显示中文 ----------
cursor = mplcursors.cursor(sc, hover=True)

@cursor.connect("add")
def _(sel):
    idx = sel.index
    name = df.iloc[idx]["产品名称"]
    sel.annotation.set_text(name)
    sel.annotation.set_fontproperties(CH_PROP)
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.85, lw=0.4)

plt.tight_layout()
plt.savefig("scatter_return_vs_sharpe_std.png", dpi=300)
print("✅ 已保存 scatter_return_vs_sharpe_std.png")
plt.show()