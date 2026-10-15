# -*- coding: utf-8 -*-
"""chart4_store.py —— 门店销售额 TOP10（含帕累托累计占比）。"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import pandas as pd
from common import *          # noqa: F401,F403

store = pd.read_csv('clean/store_clean.csv')
os.makedirs('charts', exist_ok=True)
s = store.sort_values('total_sales', ascending=False).reset_index(drop=True)
total = s['total_sales'].sum()
cum = (s['total_sales'].cumsum() / total * 100).tolist()

fig, ax1 = plt.subplots(figsize=(12, 6.4))
labels = ['%s\n(%s)' % (r['store_name'], r['store_region']) for _, r in s.iterrows()]
bars = ax1.bar(labels, s['total_sales'], color='#2f7ed8', width=0.62)
ax1.set_ylabel('6月累计销售额（元）', color='#1c5aa0')
ax1.set_title('门店销售额 TOP10 与累计占比（合计 %.0f 元）' % total, fontsize=14, pad=12)
ax1.set_ylim(0, s['total_sales'].max() * 1.18)
ax1.tick_params(axis='x', labelsize=8.5)
for b, v in zip(bars, s['total_sales']):
    ax1.text(b.get_x() + b.get_width() / 2, v, '%.0f' % v,
             ha='center', va='bottom', fontsize=8.8, color='#1c5aa0')

ax2 = ax1.twinx()
ax2.plot(labels, cum, color='#e74c3c', marker='o', markersize=6, linewidth=2)
ax2.set_ylabel('累计销售额占比（%）', color='#c0392b')
ax2.set_ylim(0, 108)
ax2.axhline(80, color='#999999', linestyle='--', linewidth=1)
for x, v in zip(labels, cum):
    ax2.text(x, v + 2.6, '%.1f%%' % v, ha='center', fontsize=8, color='#c0392b')
ax2.text(labels[-1], 81.5, '80% 线', ha='right', fontsize=8.5, color='#777777')

ax1.grid(axis='y', linestyle=':', alpha=.45)
ax1.set_axisbelow(True)
plt.tight_layout()
plt.savefig('charts/chart4_store_top10.png', bbox_inches='tight')
print('saved charts/chart4_store_top10.png')
