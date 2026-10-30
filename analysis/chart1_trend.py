# -*- coding: utf-8 -*-
"""chart1_trend.py —— 6月日销售额趋势与周末效应。

注意：上下两个子图共享 x 轴，必须使用同一套坐标。若上图用 datetime 轴、
下图用 0..29 的位置刻度，matplotlib 会把整数刻度解释成 1970 年的日期，
导致所有数据点被挤到坐标轴一端。因此这里统一改用位置索引绘图，
再用 set_xticklabels 把标签格式化成日期。
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import pandas as pd
from common import *          # noqa: F401,F403  —— 必须最先引入以配置中文字体

daily = pd.read_csv(CLEAN_DIR / 'daily_clean.csv', parse_dates=['dt'])
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

xs = list(range(len(daily)))
labels = daily['dt'].dt.strftime('%m-%d').tolist()
sales = daily['sales_amt'].tolist()
orders = daily['order_cnt'].tolist()
qty = daily['sales_qty'].tolist()
we_idx = [i for i, w in enumerate(daily['is_weekend'].tolist()) if w]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.6), sharex=True)

# ------- 上：日销售额折线 + 月均线 + 周末圈注 -------
ax1.plot(xs, sales, marker='o', color='#2f7ed8', linewidth=2,
         markersize=5, label='日销售额', zorder=3)
mean_all = float(daily['sales_amt'].mean())
ax1.axhline(mean_all, color='#e74c3c', linestyle='--', linewidth=1.4,
            label='月均 %.0f 元' % mean_all, zorder=2)
ax1.scatter([xs[i] for i in we_idx], [sales[i] for i in we_idx], s=110,
            facecolors='none', edgecolors='#e67e22', linewidths=2,
            zorder=4, label='周末')

for i, v in enumerate(sales):
    ax1.annotate('%.0f' % v, (xs[i], v), textcoords='offset points',
                 xytext=(0, 7), ha='center', fontsize=7, color='#555555')

ax1.set_ylabel('销售额（元）')
ax1.set_ylim(0, max(sales) * 1.22)
ax1.set_title('惠民零售集团 2024 年 6 月 日销售额趋势（周末效应显著）',
              fontsize=14, fontweight='bold', pad=12)
ax1.legend(loc='lower right', ncol=3, fontsize=9.5)
ax1.grid(axis='y', linestyle=':', alpha=.45)
ax1.set_axisbelow(True)

# ------- 下：订单数与销量柱状对比 -------
w = 0.4
ax2.bar([i - w / 2 for i in xs], orders, width=w, color='#f2a20c',
        label='订单数（去重时间点）')
ax2.bar([i + w / 2 for i in xs], qty, width=w, color='#41b06e',
        label='销量（交易笔数）')
ax2.set_ylabel('笔数 / 件数')
ax2.set_xlabel('业务日期')
ax2.set_xticks(xs)
ax2.set_xticklabels(labels, rotation=60, fontsize=8.5)
ax2.legend(loc='upper left', fontsize=9.5)
ax2.grid(axis='y', linestyle=':', alpha=.45)
ax2.set_axisbelow(True)
ax2.set_ylim(0, max(qty) * 1.28)

plt.tight_layout()
plt.savefig(CHARTS_DIR / 'chart1_daily_sales_trend.png', bbox_inches='tight')
print('saved charts/chart1_daily_sales_trend.png')
