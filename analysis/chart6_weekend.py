# -*- coding: utf-8 -*-
"""chart6_weekend.py —— 工作日与周末销售额分布对比（箱线图 + 均值柱）。"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import pandas as pd
from common import *          # noqa: F401,F403

daily = pd.read_csv('clean/daily_clean.csv', parse_dates=['dt'])
os.makedirs('charts', exist_ok=True)

wk = daily.loc[~daily['is_weekend'], 'sales_amt'].tolist()
we = daily.loc[daily['is_weekend'], 'sales_amt'].tolist()

fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.4))

# ① 箱线图：看分布离散程度
ax = axes[0]
bp = ax.boxplot([wk, we], labels=['工作日（20天）', '周末（10天）'],
                patch_artist=True, widths=0.45, showmeans=True,
                meanprops=dict(marker='D', markerfacecolor='#e74c3c',
                               markeredgecolor='#e74c3c', markersize=8))
for box, c in zip(bp['boxes'], ['#2f7ed8', '#f2a20c']):
    box.set_facecolor(c)
    box.set_alpha(0.75)
for med in bp['medians']:
    med.set_color('#333333')
    med.set_linewidth(2)
ax.set_ylabel('日销售额（元）')
ax.set_title('工作日与周末日销售额分布（◆ 为均值）')
ax.grid(axis='y', linestyle=':', alpha=.45)
ax.set_axisbelow(True)
for i, (data, name) in enumerate([(wk, '工作日'), (we, '周末')], start=1):
    ax.text(i, max(data) + 900, '均值 %.0f\n最高 %.0f' % (sum(data) / len(data), max(data)),
            ha='center', fontsize=9, color='#333333')
ax.set_ylim(0, max(we) * 1.30)

# ② 逐周对比：把30天按周分组，看周末拉升幅度是否稳定
ax = axes[1]
daily['week'] = daily['dt'].dt.isocalendar().week.astype(int)
weeks = sorted(daily['week'].unique())
xs = range(len(weeks))
wk_avg = [daily[(daily['week'] == w) & (~daily['is_weekend'])]['sales_amt'].mean() for w in weeks]
we_avg = [daily[(daily['week'] == w) & (daily['is_weekend'])]['sales_amt'].mean() for w in weeks]
w = 0.36
ax.bar([i - w / 2 for i in xs], wk_avg, width=w, color='#2f7ed8', label='工作日日均')
ax.bar([i + w / 2 for i in xs], we_avg, width=w, color='#f2a20c', label='周末日均')
for i, (a, b) in enumerate(zip(wk_avg, we_avg)):
    if a == a and b == b:            # 跳过 NaN（该周没有工作日或没有周末）
        ax.text(i, max(a, b) + 500, '×%.2f' % (b / a), ha='center',
                fontsize=10, color='#c0392b', fontweight='bold')
ax.set_xticks(list(xs))
ax.set_xticklabels(['第%d周' % w for w in weeks])
ax.set_ylabel('日均销售额（元）')
ax.set_title('逐周对比：周末日均 / 工作日日均 的倍数')
ax.legend(loc='upper right')
ax.grid(axis='y', linestyle=':', alpha=.45)
ax.set_axisbelow(True)
ax.set_ylim(0, max([v for v in we_avg if v == v] + [0]) * 1.28)

plt.tight_layout()
plt.savefig('charts/chart6_weekend_effect.png', bbox_inches='tight')
print('saved charts/chart6_weekend_effect.png')
