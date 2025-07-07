#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot4.py —— 主-次形态 Network-Scatter
build(df) → plotly Figure
"""

import itertools
import numpy as np
import pandas as pd                              # ← 新增
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import plotly.graph_objects as go
import matplotlib.font_manager as fm


def init_chinese_font(ttf: str = None) -> str:
    """
    一次性选择一个可用的中文字体，并注册到 Matplotlib，
    以便 Plotly 用相同名称的 font_family 时能找到。
    """
    if ttf:
        fm.fontManager.addfont(ttf)
        name = fm.FontProperties(fname=ttf).get_name()
    else:
        candidates = ["PingFang SC", "Microsoft YaHei", "SimHei", "Heiti TC"]
        installed = {f.name for f in fm.fontManager.ttflist}
        name = next((c for c in candidates if c in installed), "SimHei")
    return name


def to_float(x):
    """
    把带 %、逗号、空串、短横杠的值都转成 float 或 NaN
    """
    if isinstance(x, str):
        x = x.replace("%", "").replace(",", "").strip()
        return np.nan if x in ("", "-", "－") else float(x)
    return x


def build(df: pd.DataFrame) -> go.Figure:
    # ———— 1. 准备 & 清洗数据 ————
    font_name = init_chinese_font()

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

    # 检查列是否齐全
    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"plot4.py 缺列：{missing}")

    df2 = df.copy()
    # 转 float 并过滤掉含 NaN 的行
    df2[COLS] = df2[COLS].applymap(to_float)
    df2 = df2.dropna(subset=COLS).reset_index(drop=True)
    if df2.empty:
        raise ValueError("plot4.py：无有效数据")

    # ———— 2. 标准化 & 计算余弦相似度 ————
    X_std = StandardScaler().fit_transform(df2[COLS])
    sim = cosine_similarity(X_std)

    names = df2["产品名称"].astype(str).tolist()
    if len(names) != sim.shape[0]:
        raise ValueError("plot4.py：样本数量与相似度矩阵维度不匹配")

    # ———— 3. 构造网络 & Top-10 子图 ————
    G = nx.Graph()
    G.add_nodes_from(names)
    thresh = 0.80
    n = len(names)
    for i, j in itertools.combinations(range(n), 2):
        if sim[i, j] >= thresh:
            G.add_edge(names[i], names[j], weight=sim[i, j])

    # 取度最高的前10个节点为“核心”，再把它们的邻居也保留
    deg = dict(G.degree())
    core = sorted(deg, key=deg.get, reverse=True)[:10]
    keep = set(core)
    for node in core:
        keep.update(G.neighbors(node))
    G = G.subgraph(keep).copy()

    # ———— 4. 布局 & 数据准备 ————
    # 用一个更大的 k 值让节点推开
    pos = nx.spring_layout(G, seed=42, k=1.2, iterations=100)

    # 收集边的坐标
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    # 节点坐标 & 大小
    nodes = list(G.nodes())
    node_deg = [deg[n] for n in nodes]
    # 映射到尺寸：最小 5，最大 5 + deg*2
    node_size = [5 + d*2 for d in node_deg]

    # 分离“次要” & “核心”
    sec_x, sec_y, sec_s, sec_t = [], [], [], []
    pri_x, pri_y, pri_s, pri_t = [], [], [], []
    for n, size in zip(nodes, node_size):
        x, y = pos[n]
        if n in core:
            pri_x.append(x); pri_y.append(y); pri_s.append(size); pri_t.append(n)
        else:
            sec_x.append(x); sec_y.append(y); sec_s.append(size); sec_t.append(n)

    # ———— 5. Plotly 画图 ————
    fig = go.Figure()

    # 画边
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(color='#888', width=0.5),  # 线细一点
        hoverinfo='none',
        showlegend=False
    ))

    # 次要节点
    fig.add_trace(go.Scatter(
        x=sec_x, y=sec_y,
        mode='markers',
        name='次要节点',
        marker=dict(
            size=sec_s,
            color='#E09149',  # 浅橙
            opacity=0.6,      # 半透明
            line=dict(width=1, color='#555')
        ),
        text=sec_t,
        hoverinfo='text'
    ))

    # 核心节点
    fig.add_trace(go.Scatter(
        x=pri_x, y=pri_y,
        mode='markers',
        name='核心节点',
        marker=dict(
            size=pri_s,
            color='#8D3303',  # 深橙
            opacity=0.8,      # 比次要节点更不透明
            line=dict(width=1, color='#333')
        ),
        text=pri_t,
        hoverinfo='text'
    ))

    # 布局微调：等比坐标系、黑底白字
    fig.update_layout(
        title_text='产品主-次关系散点图（核心节点 Top-10）',
        title_x=0.5,
        font=dict(family=font_name, color='white'),
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99, xanchor="right", x=0.99,
            bgcolor='rgba(0,0,0,0)'
        ),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig