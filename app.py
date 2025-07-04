#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主页面：侧边栏选择要看的可视化模型或原始数据表，点击即切换
"""

import importlib.util
import inspect
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib
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

# ─── (2) 先读一次全量 DataFrame，用于给 plot3/plot4 传参 ──────────
@st.cache_data
def load_full_df(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

df_all = load_full_df(EXCEL_FILE)

# ─── (3) 动态 import 并智能调用 build ──────────────────────────
def load_fig_py(mod_name: str):
    file_path = PLOT_DIR / f"{mod_name}.py"
    if not file_path.exists():
        st.error(f"❌ 找不到脚本：{file_path}")
        st.stop()

    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # 优先看 build()
    if hasattr(mod, "build"):
        sig = inspect.signature(mod.build)
        # 如果 build 需要一个参数，就把 df_all 传进去
        if len(sig.parameters) == 1:
            return mod.build(df_all)
        # 否则直接无参调用
        else:
            return mod.build()
    # 回退到全局 fig
    elif hasattr(mod, "fig"):
        return mod.fig
    else:
        st.error("脚本里既没有 build() 也没有全局 fig")
        st.stop()

# ─── (4) Streamlit 页面 ───────────────────────────────────────
st.set_page_config("投资分析可视化", layout="wide")
st.title("📊 投资分析可视化 Demo")

choice = st.sidebar.radio("🔘 选择内容", list(MENU_MAP.keys()))

if MENU_MAP[choice] is None:
    st.subheader("原始数据预览")
    st.dataframe(df_all, use_container_width=True)

else:
    fig = load_fig_py(MENU_MAP[choice])

    # 如果是 matplotlib Figure，就用 st.pyplot，并强制白底黑字
    if isinstance(fig, Figure):
        # 全部白底
        fig.patch.set_facecolor("white")
        for ax in fig.axes:
            ax.set_facecolor("white")
            # 全部标签和标题强制黑
            ax.title.set_color("black")
            ax.xaxis.label.set_color("black")
            ax.yaxis.label.set_color("black")
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("black")
            # 如果有 colorbar
            for cax in getattr(fig, "get_axes", lambda:[])():
                if cax is not ax:
                    for tick in cax.get_yticklabels() + cax.get_xticklabels():
                        tick.set_color("black")
                    cax.set_facecolor("white")
        st.pyplot(fig)

    # 否则按 Plotly 处理
    else:
        st.plotly_chart(fig, use_container_width=True)

st.caption("© 2025 你的公司/姓名")