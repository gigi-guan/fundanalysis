#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主页面：侧边栏选择要看的可视化模型或原始数据表，点击即切换
"""

import importlib.util
import inspect
import traceback
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import plotly.graph_objects as go

# ─── 目录设置 ───────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
PLOT_DIR   = BASE_DIR / "models"
EXCEL_FILE = "/Users/gigiguan/Downloads/产品分析_补全版.xlsx"

# ─── (1) 菜单映射 ────────────────────────────────────────
MENU_MAP = {
    "模型 ①": "plot1",
    "模型 ②": "plot2",
    "模型 ③": "plot3",
    "模型 ④": "plot4",
    "📄 查看原始数据": None,
}

# ─── (2) 预加载全量数据 ──────────────────────────────────
@st.cache_data
def load_full_df(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

df_all = load_full_df(EXCEL_FILE)

# ─── (3) 动态加载脚本 & 执行 ─────────────────────────────
def load_plot(mod_name: str):
    file_path = PLOT_DIR / f"{mod_name}.py"
    if not file_path.exists():
        st.error(f"❌ 找不到脚本：{file_path}")
        st.stop()

    # 动态 import
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod  = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        st.error(f"🚨 {mod_name}.py 执行时出错：\n```python\n{traceback.format_exc()}```")
        st.stop()

    fig = None

    # 优先调用 build()
    if hasattr(mod, "build"):
        try:
            fn  = mod.build
            sig = inspect.signature(fn)
            # build 接收一个参数就传 df_all，否则无参
            if len(sig.parameters) == 1:
                fig = fn(df_all)
            else:
                fig = fn()
        except Exception:
            st.error(f"🚨 {mod_name}.build() 出错：\n```python\n{traceback.format_exc()}```")
            st.stop()

    # 其次尝试全局 fig
    elif hasattr(mod, "fig"):
        fig = mod.fig

    # 万一都没有，就尝试拿当前 plt.gcf()
    else:
        fig = plt.gcf()
        if fig is None:
            st.error(f"❌ 在 {mod_name}.py 中，既没有 build()，也没有 fig，导入后 plt.gcf() 也是 None。")
            st.stop()

    # 如果 build/fig 返回 None，也尝试 gcf()
    if fig is None:
        fig = plt.gcf()

    return fig

# ─── (4) Streamlit 页面 ─────────────────────────────────────
st.set_page_config("投资分析可视化", layout="wide")
st.title("📊 投资分析可视化 Demo")

choice = st.sidebar.radio("🔘 选择内容", list(MENU_MAP.keys()))

if MENU_MAP[choice] is None:
    st.subheader("原始数据预览")
    st.dataframe(df_all, use_container_width=True)

else:
    fig = load_plot(MENU_MAP[choice])

    # Matplotlib Figure
    if isinstance(fig, Figure):
        # 白底+黑字，确保在深色模式下可见
        fig.patch.set_facecolor("white")
        for ax in fig.axes:
            ax.set_facecolor("white")
            ax.title.set_color("black")
            ax.xaxis.label.set_color("black")
            ax.yaxis.label.set_color("black")
            for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                lbl.set_color("black")
        st.pyplot(fig)

    # Plotly Figure
    elif isinstance(fig, go.Figure):
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error(f"❌ 无法识别的图形类型：{type(fig)}")

st.caption("© 2025")