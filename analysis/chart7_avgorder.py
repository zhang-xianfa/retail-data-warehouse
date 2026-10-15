# -*- coding: utf-8 -*-
"""chart7_avgorder.py —— 日销售额与客单价的关系（双轴折线 + 散点拟合）。"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import numpy as np
import pandas as pd
from common import *          # noqa: F401,F403

daily = pd.read_csv('clean/daily_clean.csv', parse_dates=['dt'])
os.makedirs('charts', exist_ok=True)

d = daily.dropna(subset=['avg_order_amt']).reset_index(drop=True)
xs = list(range(len(d)))
labels = d['dt'].dt.strftime('%m-%d').tolist()

fig, axes = plt.subplots(1, 2, figsize=(14.6, 5.4),
                         gridspec_kw={'width_ratios': [2.1, 1]})

# ① 双轴：销售额（柱）与客单价（线）
ax1 = axes[0]
ax1.bar(xs, d['sales_amt'], color='#cfe0f5', width=0.62, label='日销售额')
ax1.set_ylabel('日销售额（元）', color='#1c5aa0')
ax1.set_ylim(0, d['sales_amt'].max() * 1.22)
ax1.set_xticks(xs)
ax1.set_xticklabels(labels, rotation=60, fontsize=8)
ax1.grid(axis='y', linestyle=':', alpha=.4)
ax1.set_axisbelow(True)

ax2 = ax1.twinx()
ax2.plot(xs, d['avg_order_amt'], color='#e74c3c', marker='o',
         markersize=4.5, linewidth=1.8, label='客单价')
ax2.axhline(float(d['avg_order_amt'].mean()), color='#e74c3c',
            linestyle='--', linewidth=1, alpha=.6)
ax2.set_ylabel('客单价（元）', color='#c0392b')
ax2.set_ylim(0, d['avg_order_amt'].max() * 1.35)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=9)
ax1.set_title('日销售额与客单价走势（客单价均值 %.2f 元）'
              % d['avg_order_amt'].mean(), fontsize=13)

# ② 散点：订单数 vs 销售额，看规模由什么驱动
ax = axes[1]
x = d['order_cnt'].astype(float).values
y = d['sales_amt'].astype(float).values
ax.scatter(x, y, s=62, c=['#f2a20c' if w else '#2f7ed8' for w in d['is_weekend']],
           alpha=.85, edgecolors='white', linewidths=1.1, zorder=3)
k, b = np.polyfit(x, y, 1)
xr = np.linspace(x.min(), x.max(), 50)
ax.plot(xr, k * xr + b, color='#e74c3c', linewidth=1.6, linestyle='--',
        label='拟合：销售额 ≈ %.0f×订单数 + %.0f' % (k, b))
r = np.corrcoef(x, y)[0, 1]
ax.set_xlabel('当日订单数（单）')
ax.set_ylabel('当日销售额（元）')
ax.set_title('订单数—销售额散点（相关系数 r=%.3f）' % r, fontsize=13)
ax.legend(loc='lower right', fontsize=8.5)
ax.grid(linestyle=':', alpha=.45)
ax.set_axisbelow(True)

import matplotlib.patches as mpatches
ax.legend(handles=[mpatches.Patch(color='#2f7ed8', label='工作日'),
                   mpatches.Patch(color='#f2a20c', label='周末'),
                   plt.Line2D([], [], color='#e74c3c', linestyle='--',
                              label='线性拟合 r=%.3f' % r)],
          loc='lower right', fontsize=8.5)

plt.tight_layout()
plt.savefig('charts/chart7_avg_order.png', bbox_inches='tight')
print('saved charts/chart7_avg_order.png  (r=%.3f)' % r)
