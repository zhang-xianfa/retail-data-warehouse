# -*- coding: utf-8 -*-
"""chart5_pay.py —— 支付方式分布（笔数 + 金额占比）。"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import pandas as pd
from common import *          # noqa: F401,F403

pay = pd.read_csv(CLEAN_DIR / 'pay_clean.csv')
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

order = ['微信支付', '支付宝', '现金']
pay['_o'] = pay['pay_type'].map({k: i for i, k in enumerate(order)}).fillna(99)
pay = pay.sort_values('_o').drop(columns='_o').reset_index(drop=True)

fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.2))

# ① 交易笔数
ax = axes[0]
bars = ax.bar(pay['pay_type'], pay['trade_cnt'], color=COLORS[:len(pay)], width=0.55)
ax.set_ylabel('交易笔数')
ax.set_title('各支付方式交易笔数（合计 %d 笔）' % int(pay['trade_cnt'].sum()))
for b, v, p in zip(bars, pay['trade_cnt'], pay['cnt_pct']):
    ax.text(b.get_x() + b.get_width() / 2, v, '%d 笔\n%.1f%%' % (v, p),
            ha='center', va='bottom', fontsize=9.5)
ax.set_ylim(0, pay['trade_cnt'].max() * 1.28)
ax.grid(axis='y', linestyle=':', alpha=.45)
ax.set_axisbelow(True)

# ② 金额占比
ax = axes[1]
wedges, _t, autot = ax.pie(
    pay['total_amount'], labels=pay['pay_type'], colors=COLORS[:len(pay)],
    autopct='%1.2f%%', startangle=90, counterclock=False,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2))
for t in autot:
    t.set_fontsize(10)
ax.set_title('各支付方式交易金额占比')

plt.tight_layout()
plt.savefig(CHARTS_DIR / 'chart5_pay_type.png', bbox_inches='tight')
print('saved charts/chart5_pay_type.png')
