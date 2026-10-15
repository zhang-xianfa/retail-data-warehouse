# -*- coding: utf-8 -*-
"""chart2_region.py —— 各大区销售额、门店数、单店均值对比。"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import pandas as pd
from common import *          # noqa: F401,F403

region = pd.read_csv('clean/region_clean.csv')
os.makedirs('charts', exist_ok=True)
total = region['total_sales'].sum()

fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2))

# ① 销售额（含占比）
ax = axes[0]
bars = ax.bar(region['region'], region['total_sales'], color=COLORS[:len(region)], width=0.55)
ax.set_ylabel('销售额（元）')
ax.set_title('各大区销售额（合计 %.0f 元）' % total)
for b, v in zip(bars, region['total_sales']):
    ax.text(b.get_x() + b.get_width() / 2, v,
            '%.0f\n%.1f%%' % (v, v / total * 100), ha='center', va='bottom', fontsize=9.5)
ax.set_ylim(0, region['total_sales'].max() * 1.28)

# ② 门店数 vs 单店均值（回答"是大区门店多，还是单店强"）
ax = axes[1]
x = range(len(region))
bars = ax.bar([i - 0.2 for i in x], region['store_avg'], width=0.4,
              color='#2f7ed8', label='单店平均销售额（元）')
ax2 = ax.twinx()
ax2.bar([i + 0.2 for i in x], region['store_cnt'], width=0.4,
        color='#f2a20c', label='门店数（家）')
ax2.set_ylim(0, region['store_cnt'].max() * 1.6)
ax2.set_ylabel('门店数（家）', color='#c07d00')
ax.set_xticks(list(x))
ax.set_xticklabels(region['region'])
ax.set_ylabel('单店平均销售额（元）', color='#1c5aa0')
ax.set_title('门店数与单店产出对比')
for i, v in enumerate(region['store_avg']):
    ax.text(i - 0.2, v, '%.0f' % v, ha='center', va='bottom', fontsize=9)
for i, v in enumerate(region['store_cnt']):
    ax2.text(i + 0.2, v, '%d家' % v, ha='center', va='bottom', fontsize=9, color='#c07d00')
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc='upper right', fontsize=8.5)

# ③ 销量占比环形图
ax = axes[2]
wedges, _t, autot = ax.pie(
    region['total_qty'], labels=region['region'], colors=COLORS[:len(region)],
    autopct='%1.1f%%', startangle=90, counterclock=False,
    wedgeprops=dict(width=0.42, edgecolor='white', linewidth=2))
for t in autot:
    t.set_fontsize(10)
ax.set_title('各大区销量占比')

plt.tight_layout()
plt.savefig('charts/chart2_region_sales.png', bbox_inches='tight')
print('saved charts/chart2_region_sales.png')
