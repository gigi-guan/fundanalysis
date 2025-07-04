#!/usr/bin/env python3
# coding: utf-8
"""
读取《产品分析_补全版.xlsx》，计算皮尔逊相关系数，
绘制 3-D 曲面热力图（中文友好）。
依赖：pandas  numpy  matplotlib  seaborn  pyplotz
"""

import argparse, sys, datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D           # noqa: F401
from matplotlib.colors import Normalize
import matplotlib.font_manager as fm
from pyplotz.pyplotz import PyplotZ

# -------- 0. 因子列 ----------
COLS_RAW = [
    "最近一年（含2025年）的年化", "过去3年平均年化", "过去3年累计回报",
    "2024年年化", "2023年年化", "2022年年化", "2021年年化", "2020年年化",
    "基金标准差", "投资组合预期年化报酬率",
    "年化无风险利率（平均回报减去预期年化的绝对值）",
    "夏普比率", "最大回撤", "卡玛比率",
]
ALIAS_MAP = {
    "最近一年（含2025年）的年化": "近1Y年化",
    "过去3年平均年化": "3Y平均年化",
    "过去3年累计回报": "3Y累计回报",
    "投资组合预期年化报酬率": "组合预期年化",
    "年化无风险利率（平均回报减去预期年化的绝对值）": "无风险年化",
}

# -------- 1. 字体处理 ----------
def init_chinese_font(ttf: str | Path | None = None) -> str:
    """注册指定 ttf，或自动回退系统中文黑体；返回实际生效名字"""
    if ttf and Path(ttf).expanduser().exists():
        fp = Path(ttf).expanduser()
        fm.fontManager.addfont(str(fp))
        font_name = fm.FontProperties(fname=str(fp)).get_name()
    else:
        cand = ["PingFang SC", "Heiti TC", "Microsoft YaHei", "SimHei"]
        font_name = next(
            (c for c in cand if any(c in p for p in fm.findSystemFonts())), "SimHei"
        )
    plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False
    return font_name


# -------- 2. 读取 & 清洗 ----------
def load_excel(path: Path, cols_raw: list[str]) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_excel(path, dtype=str)
    miss = [c for c in cols_raw if c not in df.columns]
    if miss:
        sys.exit(f"❌ Excel 缺少列：{miss}")

    df = df.rename(columns=ALIAS_MAP)
    cols = [ALIAS_MAP.get(c, c) for c in cols_raw]

    for c in cols:
        df[c] = (df[c].str.replace("%", "")
                         .str.replace(",", "")
                         .replace({"-": np.nan, "": np.nan})
                         .astype(float))
    df = df.dropna(subset=cols)
    return df, cols


# -------- 3. 画 3-D 曲面 ----------
def draw_3d(df: pd.DataFrame, cols: list[str], out_png: Path):
    corr = df[cols].corr()
    n = len(cols)
    X, Y = np.meshgrid(range(n), range(n))
    Z = corr.values

    norm   = Normalize(vmin=-1, vmax=1)
    colors = cm.coolwarm(norm(Z))

    PyplotZ()                             # 读取 rcParams 字体
    prop = fm.FontProperties(family=plt.rcParams["font.family"], size=8)

    fig = plt.figure(figsize=(12,10))
    ax  = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z,
                    facecolors=colors,
                    rstride=1, cstride=1,
                    linewidth=0, antialiased=False, shade=False)

    ax.set_zlim(-1, 1)
    ax.set_zlabel("相关系数", fontproperties=prop)

    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(cols, fontproperties=prop, rotation=60, ha="right")
    ax.set_yticklabels(cols, fontproperties=prop)

    # 色条
    mappable = cm.ScalarMappable(norm=norm, cmap="coolwarm")
    mappable.set_array([])
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.6, pad=0.08)
    cbar.ax.set_ylabel("相关系数", fontproperties=prop)
    for t in cbar.ax.get_yticklabels(): t.set_fontproperties(prop)

    PyplotZ().title("各因子皮尔逊相关系数 — 3D 立体热力图", fontsize=16)
    plt.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.show()
    print(f"✅ 已保存 → {out_png.resolve()}")


# -------- 4. CLI ----------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("-f", "--file", default="/Users/gigiguan/Downloads/产品分析_补全版.xlsx", help="Excel 文件")
    p.add_argument("-o", "--output", help="输出 PNG")
    p.add_argument("--font", default="~/Library/Fonts/plot_zh.ttf", help="中文 ttf 路径")
    args = p.parse_args()

    init_chinese_font(args.font)
    excel = Path(args.file).expanduser()
    out   = Path(args.output).expanduser() if args.output \
           else excel.with_name(f"heatmap3d_{dt.datetime.now():%Y%m%d_%H%M%S}.png")

    df, cols = load_excel(excel, COLS_RAW)
    if df.empty:
        sys.exit("❌ 清洗后无有效数据。")
    draw_3d(df, cols, out)


if __name__ == "__main__":
    main()