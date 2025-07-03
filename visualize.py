# visualize_scatter.py

import pandas as pd
# ---------------------------------------------------------------------------
# 固定指定 1 个中文字体文件，不依赖系统字体是否能被 matplotlib 识别
# （适用于 macOS / Linux / Windows，一次设置终身受用）
# ---------------------------------------------------------------------------
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
import os, sys

# ① 先把一份明确可用的中文字体准备好 ----------------------------
# 建议下载：NotoSansSC-Regular.otf   （Google 开源，干净无版权问题）
# https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf
# 假设你把它放在：  ~/fonts/NotoSansSC-Regular.otf
font_path = os.path.expanduser("~/fonts/NotoSansSC-Regular.otf")   # ← 改成你的真实路径
if not os.path.exists(font_path):
    sys.exit(f"[❌] 找不到字体文件: {font_path}\n  请先下载并把路径改对，再运行脚本")

# ② 手动把这份字体注册进 matplotlib ----------------------------
prop = FontProperties(fname=font_path)            # prop.get_name() 会返回字体内部名称
font_name = prop.get_name()                       # 例如 "Noto Sans SC"
if font_name not in [f.name for f in fontManager.ttflist]:
    fontManager.addfont(font_path)                # 动态注册
    matplotlib.font_manager._rebuild()            # 刷新 fontManager 缓存

# ③ 设置全局中文 & 负号 ----------------------------
plt.rcParams['font.sans-serif'] = [font_name]     # 把咱们这份字体设为首选
plt.rcParams['axes.unicode_minus'] = False
print(f"[matplotlib] 当前中文字体: {font_name}")

# ---------------------------------------------------------------------------
# 下面开始你的正常绘图代码
# ---------------------------------------------------------------------------
# …… 你的 pandas / seaborn 绘图……
import seaborn as sns



# 1. 读取数据
df = pd.read_excel(
    "/Users/gigiguan/Downloads/产品分析_补全版.xlsx",
    dtype=str
)

# 2. 选取并清洗因子（纯数字列）
factors = {
    "年化收益2025":    "最近一年（含2025年）的年化",
    "3年平均年化":     "过去3年平均年化",
    "标准差":         "基金标准差",
    "夏普比率":       "夏普比率",
    "最大回撤":       "最大回撤"
}
for alias, col in factors.items():
    df[alias] = (
        df[col]
        .str.replace('%','', regex=False)
        .str.replace(',','', regex=False)
        .astype(float)
    )

# 丢弃任何缺失值
df = df.dropna(subset=list(factors.keys()))

# 3. 绘制散点图
plt.figure(figsize=(10,8))
sns.set_style("whitegrid", {"grid.linestyle":"--"})

sc = plt.scatter(
    x = df["年化收益2025"],
    y = df["3年平均年化"],
    c = df["夏普比率"],
    s = df["标准差"] * 20,     # 点大小映射为波动率
    cmap = "viridis",
    alpha = 0.7,
    edgecolors = "white",
    linewidths = 0.5
)

cbar = plt.colorbar(sc)
cbar.set_label("夏普比率", fontsize=12)

plt.title("最近一年年化 vs 过去3年平均年化\n（点色=夏普，比大小=波动率）", fontsize=16)
plt.xlabel("2025年年化收益（%）", fontsize=14)
plt.ylabel("过去3年平均年化（%）", fontsize=14)

plt.tight_layout()
plt.savefig("scatter_return_vs_sharpe_std.png", dpi=300)
plt.show()