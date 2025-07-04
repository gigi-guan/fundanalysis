#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot4.py —— 主-次形态  Network-Scatter
1. 读取《产品分析_补全版.xlsx》
2. 8 个关键因子做余弦相似度
3. 按相似度≥threshold 连边 → 取 Top-N 核心节点 + 1 阶邻居
4. 绘中文网络散点图并保存
------------------------------------------------------------
依赖：pandas  numpy  scikit-learn  networkx  matplotlib  pyplotz
用法：
    python plot4.py \
        -f ~/Downloads/产品分析_补全版.xlsx \
        -o network_core_scatter.png \
        --font ~/Library/Fonts/PingFang.ttc
"""

import argparse, itertools, sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import to_hex
from pyplotz.pyplotz import PyplotZ

# ---------- 0. 字体工具 --------------------------------- #
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from pathlib import Path

def _font_exist(family: str) -> bool:
    """在已扫描字体表里找 family 名字，避免逐文件加载。"""
    return any(fe.name == family for fe in fm.fontManager.ttflist)

def init_chinese_font(ttf: str | Path | None = None) -> str:
    """
    先用用户指定 TTF/OTF；若未指定就依次尝试系统里的常见中文黑体。
    全程不再逐文件加载，避免 ‘invalid pixel size’ 异常。
    """
    if ttf and Path(ttf).expanduser().is_file():
        fp = Path(ttf).expanduser()
        fm.fontManager.addfont(str(fp))
        name = fm.FontProperties(fname=str(fp)).get_name()
    else:
        cand = ["PingFang SC", "Microsoft YaHei", "SimHei", "Heiti TC"]
        name = next((f for f in cand if _font_exist(f)), "SimHei")

    plt.rcParams["font.family"] = name
    plt.rcParams["axes.unicode_minus"] = False
    return name


# ---------- 1. 清洗工具 --------------------------------- #
def to_float(x):
    if isinstance(x, str):
        x = x.replace("%", "").replace(",", "").strip()
        return np.nan if x in ("", "-", "－") else float(x)
    return x


# ---------- 2. 可视化主函数 ----------------------------- #
def draw_network(df: pd.DataFrame, cols: list[str], out_png: Path, font_name: str):
    # 2.1 余弦相似度
    X_std = StandardScaler().fit_transform(df[cols])
    sim   = cosine_similarity(X_std)

    # 2.2 构图
    names = df["产品名称"].tolist() if "产品名称" in df.columns else df.index.astype(str).tolist()

    threshold = .80
    G = nx.Graph()
    G.add_nodes_from(names)

    for i, j in itertools.combinations(range(len(names)), 2):
        if sim[i, j] >= threshold:
            G.add_edge(names[i], names[j], weight=sim[i, j])

    # 2.3 核心节点
    deg = dict(G.degree())
    core_num   = 10
    core_nodes = sorted(deg, key=deg.get, reverse=True)[:core_num]

    keep = set(core_nodes)
    for n in core_nodes:
        keep.update(G.neighbors(n))
    G = G.subgraph(keep).copy()

    # 2.4 可视属性
    max_deg = max(deg[n] for n in G.nodes) if G.nodes else 1
    node_sizes = [80 + deg[n] * 20 for n in G.nodes]
    node_colors = [
        to_hex(plt.cm.Oranges(.3 + .7 * deg[n] / max_deg)) for n in G.nodes
    ]

    pos = nx.spring_layout(G, seed=42, k=.35)

    # 2.5 画
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_title("产品主-次关系散点图（核心节点 Top-10）", fontsize=16, fontfamily=font_name, pad=15)
    ax.axis("off")

    nx.draw_networkx_edges(G, pos, alpha=.25, width=.8, edge_color="#999999", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                           edgecolors="#555555", linewidths=.5, ax=ax)

    labels = {n: n for n in core_nodes}
    nx.draw_networkx_labels(
        G, pos, labels=labels,
        font_family=font_name, font_size=9,
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#333333", lw=.4, alpha=.85),
        verticalalignment="center", horizontalalignment="center", ax=ax
    )

    plt.tight_layout()
    fig.savefig(out_png, dpi=300)
    print(f"✅ 已保存图像：{out_png.resolve()}")
    plt.show()


# ---------- 3. CLI ------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="8 因子余弦相似度 · 中文网络散点")
    parser.add_argument("-f", "--file", default="/Users/gigiguan/Downloads/产品分析_补全版.xlsx", help="Excel 文件")
    parser.add_argument("-o", "--output", default=None, help="输出 PNG 路径")
    parser.add_argument("--font", default=None, help="指定中文 TTF/OTF 路径")
    args = parser.parse_args()

    font_name = init_chinese_font(args.font)

    excel_path = Path(args.file).expanduser()
    if not excel_path.is_file():
        sys.exit(f"❌ 找不到文件：{excel_path}")

    cols = [
        "最近一年（含2025年）的年化",
        "过去3年平均年化",
        "过去3年累计回报",
        "基金标准差",
        "夏普比率",
        "最大回撤",
        "2024年年化",
        "投资组合预期年化报酬率",
    ]
    df = pd.read_excel(excel_path, dtype=str)
    for c in cols:
        if c not in df.columns:
            sys.exit(f"❌ 缺少列：{c}")
        df[c] = df[c].apply(to_float)
    df = df.dropna(subset=cols)
    if df.empty:
        sys.exit("❌ 无有效数据可绘制网络图。")

    out_png = (
        Path(args.output).expanduser()
        if args.output
        else excel_path.with_name("network_core_scatter.png")
    )
    draw_network(df, cols, out_png, font_name)


if __name__ == "__main__":
    main()