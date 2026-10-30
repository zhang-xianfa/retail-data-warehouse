# -*- coding: utf-8 -*-
"""common.py —— matplotlib 中文字体与统一绘图风格配置。

所有绘图脚本必须在最前面 import 本模块，保证字体配置先生效；
否则图表中的中文会渲染成方块（豆腐块）。
"""
from pathlib import Path

import matplotlib

matplotlib.use('Agg')            # 无界面后端：直接存文件，不弹窗

import matplotlib.pyplot as plt
import seaborn as sns

# 注意顺序：sns.set_style() 会把 font.sans-serif 重置回 Arial/DejaVu Sans，
# 因此中文字体必须在 set_style 之后再设置，否则中文会渲染成方块。
sns.set_style('whitegrid')

plt.rcParams['font.sans-serif'] = ['SimHei']      # 中文字体：黑体
plt.rcParams['axes.unicode_minus'] = False        # 正常显示负号
plt.rcParams['figure.dpi'] = 120
plt.rcParams['savefig.dpi'] = 140
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.titleweight'] = 'bold'

# 全站统一配色
COLORS = ['#2f7ed8', '#41b06e', '#f2a20c', '#e74c3c', '#9b59b6', '#16a085']
CAT_COLORS = {'生鲜': '#41b06e', '日用品': '#2f7ed8', '家电': '#f2a20c'}

# ── 仓库内路径：脚本从任意目录运行都能找到数据与输出目录 ──
ROOT_DIR = Path(__file__).resolve().parents[1]   # 仓库根目录
DATA_DIR = ROOT_DIR / 'data'                     # Hive 导出的原始 CSV
CLEAN_DIR = DATA_DIR / 'clean'                   # 清洗后的 CSV
CHARTS_DIR = ROOT_DIR / 'analysis' / 'charts'    # 图表输出
