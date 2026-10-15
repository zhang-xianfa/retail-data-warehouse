# -*- coding: utf-8 -*-
"""chart3_goods.py —— 商品销售额 TOP10（按品类着色）。"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import pandas as pd
from common import *          # noqa: F401,F403

goods = pd.read_csv('clean/goods_clean.csv')
os.makedirs('charts', exist_ok=True)
g = goods.sort_values('total_sales')          # 横向条形图：从小到大排，最长的在最上面
total = goods['total_sales'].sum()

fig, ax = plt.subplots(figsize=(11.5, 6.6))
colors = [CAT_COLORS.get(c, '#95a5a6') for c in g['category_name']]
bars = ax.barh(g['goods_name'], g['total_sales'], color=colors, height=0.62)
ax.set_xlabel('6月累计销售额（元）')
ax.set_title('商品销售额 TOP10（按品类着色，合计 %.0f 元）' % total, fontsize=14, pad=12)
ax.set_xlim(0, g['total_sales'].max() * 1.32)
for b, (_, r) in zip(bars, g.iterrows()):
    ax.text(b.get_width(), b.get_y() + b.get_height() / 2,
            ' %.0f 元 / %d 件' % (r['total_sales'], r['total_qty']),
            va='center', fontsize=9, color='#333333')

import matplotlib.patches as mpatches
handles = [mpatches.Patch(color=v, label=k) for k, v in CAT_COLORS.items()]
ax.legend(handles=handles, loc='lower right', title='品类', fontsize=9.5)
ax.grid(axis='x', linestyle=':', alpha=.45)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('charts/chart3_goods_top10.png', bbox_inches='tight')
print('saved charts/chart3_goods_top10.png')
