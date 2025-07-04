#!/usr/bin/env python3
# coding: utf-8
"""
读取《产品分析_补全版.xlsx》，计算所选因子皮尔逊相关系数并绘制中文热力图
依赖：pandas seaborn matplotlib pyplotz numpy
用法：python plot2.py -f 文件.xlsx [-o out.png] [--font ~/xxx.ttf]
"""

import argparse, sys, datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pyplotz.pyplotz import PyplotZ

# ------------------------- 0. 配置列 & 别名 --------------------------
COLS_RAW = [
    "最近一年（含2025年）的年化",
    "过去3年平均年化",
    "过去3年累计回报",
    "2024年年化","2023年年化","2022年年化","2021年年化","2020年年化",
    "基金标准差",
    "投资组合预期年化报酬率",
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

# ------------------------- 1. 中文字体 -------------------------------
def _init_chinese_font(ttf: str | Path | None = None) -> str:
    """
    1) 如果传入 ttf/otf 路径且存在 → 手动注册并返回字体名
    2) 如果传入系统字体名 → 直接返回
    3) 否则在常见中文黑体里自动寻找
    """
    fallback = ["PingFang SC", "Heiti TC", "Microsoft YaHei", "SimHei"]

    if ttf:
        ttf = Path(ttf).expanduser()
        if ttf.suffix.lower() in {".ttf", ".otf"} and ttf.exists():
            fm.fontManager.addfont(str(ttf))
            font_name = fm.FontProperties(fname=str(ttf)).get_name()
        else:
            font_name = str(ttf)          # 可能本身就是字体名
    else:
        font_name = ""

    if font_name and font_name in matplotlib.font_manager.get_font_names():
        pass                    # OK
    else:                       # fallback
        font_name = next(
            (f for f in fallback if f in matplotlib.font_manager.get_font_names()),
            fallback[-1]
        )

    plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False
    return font_name

# ------------------------- 2. 读 & 清洗 -----------------------------
def load_and_clean(excel: Path, cols_raw: list[str]) -> tuple[pd.DataFrame, list[str]]:
    if not excel.exists():
        sys.exit(f"❌ 找不到文件：{excel}")

    df = pd.read_excel(excel, dtype=object)  # 用 object 最通用

    miss = [c for c in cols_raw if c not in df.columns]
    if miss:
        sys.exit(f"❌ Excel 缺少列：{miss}")

    df = df.rename(columns=ALIAS_MAP)
    cols = [ALIAS_MAP.get(c, c) for c in cols_raw]

    for c in cols:
        df[c] = (
            df[c].astype(str)
                 .str.replace("%", "", regex=False)
                 .str.replace(",", "", regex=False)
                 .replace({"-": np.nan, "": np.nan})
                 .pipe(pd.to_numeric, errors="coerce")
        )

    df = df.dropna(subset=cols)
    return df, cols

# ------------------------- 3. 绘图 -------------------------------
def draw_heatmap(df: pd.DataFrame, cols: list[str], out_png: Path, ch_font: str):
    corr = df[cols].corr("pearson")

    #mask = np.triu(np.ones_like(corr, dtype=bool))   # 只保留下三角
    #mask = ~mask                                     # 反转，显示下三角
    mask = np.zeros_like(corr, dtype=bool)

    pltz = PyplotZ()
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.set_theme(style="white")

    ch_prop = fm.FontProperties(family=ch_font)

    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f",
        cmap="coolwarm", center=0, square=True, linewidths=.5,
        cbar_kws={"shrink": .8, "label": "相关系数"},
        annot_kws={"fontsize": 9, "fontproperties": ch_prop},
        ax=ax,
    )

    ax.set_xticklabels(ax.get_xticklabels(), rotation=60, ha="right", fontsize=9, fontproperties=ch_prop)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=9, fontproperties=ch_prop)

    # 调整 colorbar 字体
    cbar_ax = ax.collections[0].colorbar.ax
    cbar_ax.yaxis.label.set_fontproperties(ch_prop)
    for t in cbar_ax.get_yticklabels():
        t.set_fontproperties(ch_prop)

    pltz.title("各因子皮尔逊相关系数矩阵", fontsize=18)
    plt.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.show()
    print(f"✅ 已保存：{out_png.resolve()}")

# ------------------------- 4. CLI -------------------------------
def main():
    parser = argparse.ArgumentParser(description="绘制因子相关系数热力图")
    parser.add_argument("-f", "--file", default="/Users/gigiguan/Downloads/产品分析_补全版.xlsx", help="Excel 文件路径")
    parser.add_argument("-o", "--output", help="输出 PNG 路径")
    parser.add_argument("--font", default="~/Library/Fonts/plot_zh.ttf", help="自定义中文 ttf 或系统字体名")
    args = parser.parse_args()

    font_in_use = _init_chinese_font(args.font)

    excel_path = Path(args.file).expanduser()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_png = Path(args.output).expanduser() if args.output else excel_path.with_name(f"{excel_path.stem}_{timestamp}.png")

    df, cols = load_and_clean(excel_path, COLS_RAW)
    if df.empty:
        sys.exit("❌ 清洗后无有效数据，无法绘制。")

    draw_heatmap(df, cols, out_png, font_in_use)

if __name__ == "__main__":
    main()