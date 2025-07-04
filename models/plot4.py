#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot4.py —— 主-次形态 Network-Scatter
build(df) → Matplotlib Figure
"""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from matplotlib.figure import Figure as MplFigure
import matplotlib.font_manager as fm

COLS = [
    "最近一年（含2025年）的年化",
    "过去3年平均年化",
    "过去3年累计回报",
    "基金标准差",
    "夏普比率",
    "最大回撤",
    "2024年年化",
    "投资组合预期年化报酬率",
]

def init_chinese_font(ttf: str | Path | None = None) -> str:
    if ttf and Path(ttf).expanduser().is_file():
        fm.fontManager.addfont(str(Path(ttf).expanduser()))
        name = fm.FontProperties(fname=str(Path(ttf).expanduser())).get_name()
    else:
        cand = ["PingFang SC","Microsoft YaHei","SimHei","Heiti TC"]
        installed = [f.name for f in fm.fontManager.ttflist]
        name = next((c for c in cand if c in installed), "SimHei")
    plt.rcParams["font.family"] = name
    plt.rcParams["axes.unicode_minus"] = False
    return name

def to_float(x):
    if isinstance(x, str):
        x = x.replace("%","").replace(",","").strip()
        return np.nan if x in ("","-","－") else float(x)
    return x

def build(df: pd.DataFrame) -> MplFigure:
    """
    供 app.py 调用，返回 Matplotlib Figure
    """
    font_name = init_chinese_font()
    # 准备数据
    df2 = df.copy()
    for c in COLS:
        if c not in df2.columns:
            raise ValueError(f"plot4.py 缺列：{c}")
        df2[c] = df2[c].apply(to_float)
    df2 = df2.dropna(subset=COLS)
    if df2.empty:
        raise ValueError("plot4.py：无有效数据")

    X_std = StandardScaler().fit_transform(df2[COLS])
    sim = cosine_similarity(X_std)
    names = df2.get("产品名称", df2.index).astype(str).tolist()

    # 构造网络
    G = nx.Graph()
    G.add_nodes_from(names)
    thresh = 0.80
    for i, j in itertools.combinations(range(len(names)), 2):
        if sim[i, j] >= thresh:
            G.add_edge(names[i], names[j], weight=sim[i, j])

    deg = dict(G.degree())
    core = sorted(deg, key=deg.get, reverse=True)[:10]
    keep = set(core)
    for n in core:
        keep.update(G.neighbors(n))
    G = G.subgraph(keep).copy()

    max_deg = max(deg[n] for n in G.nodes) if G.nodes else 1
    sizes = [80 + deg[n]*20 for n in G.nodes]
    colors = [to_hex(plt.cm.Oranges(0.3 + 0.7*deg[n]/max_deg)) for n in G.nodes]
    pos = nx.spring_layout(G, seed=42, k=0.35)

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_title("产品主-次关系散点图（核心节点 Top-10）", fontfamily=font_name, fontsize=16, pad=15)
    ax.axis("off")

    nx.draw_networkx_edges(G, pos, alpha=0.25, width=0.8, edge_color="#999999", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors, edgecolors="#555", linewidths=0.5, ax=ax)
    labels = {n: n for n in core}
    nx.draw_networkx_labels(
        G, pos, labels=labels, font_family=font_name, font_size=9,
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#333", lw=0.4, alpha=0.85),
        ax=ax
    )
    plt.tight_layout()
    return fig