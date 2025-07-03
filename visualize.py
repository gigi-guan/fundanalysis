# visualize_scatter.py

import os, sys
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from pyplotz.pyplotz import PyplotZ
import seaborn as sns
import mplcursors

# 1. 启用中文
pltz = PyplotZ()
pltz.enable_chinese()

ch_font = matplotlib.rcParams['font.sans-serif'][0]
ch_prop = FontProperties(family=ch_font)

# 2. 读数据
excel_path = "/Users/gigiguan/Downloads/产品分析_补全版.xlsx"
if not os.path.exists(excel_path):
    sys.exit(f"❌ 找不到文件：{excel_path}")
df = pd.read_excel(excel_path, dtype=str)

# 3. 清洗
factors = {
    "年化收益2025": "最近一年（含2025年）的年化",
    "3年平均年化":  "过去3年平均年化",
    "标准差":      "基金标准差",
    "夏普比率":    "夏普比率",
    "最大回撤":    "最大回撤",
}
for alias, col in factors.items():
    df[alias] = (df[col]
        .str.replace('%', '', regex=False)
        .str.replace(',', '', regex=False)
        .astype(float))
df = df.dropna(subset=list(factors.keys()))

# 4. 绘点
plt.figure(figsize=(10, 8))
sns.set_style("whitegrid", {"grid.linestyle": "--"})
sc = plt.scatter(
    x=df["年化收益2025"],
    y=df["3年平均年化"],
    c=df["夏普比率"],
    s=df["标准差"] * 20,
    cmap="viridis",
    alpha=0.7,
    edgecolors="white",
    linewidths=0.5,
)

# 5. colorbar
cbar = plt.colorbar(sc)
cbar.set_label("Sharpe Ratio", fontproperties=ch_prop, fontsize=12)

# 6. 标题/轴
pltz.title("最近一年年化 vs 过去3年平均年化\n（点色=夏普，比大小=波动率）", fontsize=16)
pltz.xlabel("最近一年年化（%）", fontsize=14)
pltz.ylabel("过去3年平均年化（%）", fontsize=14)

# 7. hover 显示名称 —— 关键在这里
cursor = mplcursors.cursor(sc, hover=True)
@cursor.connect("add")
def _(sel):
    idx = sel.index                # mplcursors v0.6+ 提供 .index
    name = df.iloc[idx]["产品名称"]
    sel.annotation.set_text(name)  # 先填中文
    sel.annotation.set_fontproperties(ch_prop)  # 再给 annotation 单独设中文字体
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

plt.tight_layout()
plt.savefig("scatter_return_vs_sharpe_std.png", dpi=300)
plt.show()