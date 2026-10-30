# -*- coding: utf-8 -*-
"""
data_clean.py —— 读取 Hive 导出的 5 份原始 CSV，完成清洗并输出到 clean/ 目录。

清洗动作：
  1) 指定列名（Hive 导出文件不含表头）；
  2) 数值列统一转数值类型：空串 / 'NULL' / '\\N' 一律视为缺失（NaN）；
  3) 日销售按自然日 reindex 补全（缺日补 0），保证趋势图横轴连续；
  4) 用 IQR 法识别日销售额异常值并打标（不直接删除，保留供分析）；
  5) 文本列的缺失用业务默认值填充（未知商品 / 未知门店）；
  6) 派生客单价、金额占比等指标列；
  7) 结果以 utf-8-sig 编码写出，便于 Excel 直接打开不乱码。
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import pandas as pd

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW = ROOT_DIR / 'data'          # Hive 导出的原始 CSV
CLEAN = ROOT_DIR / 'data' / 'clean'  # 清洗后的 CSV（与仓库目录结构一致）
os.makedirs(CLEAN, exist_ok=True)

# Hive 导出的 NULL 可能表现为空串、'NULL' 或 '\N'，统一归为缺失
NULL_TOKENS = ['', 'NULL', 'null', '\\N', 'None', 'nan']


def load(name, columns, numeric):
    """读取一份导出 CSV；columns 指定列名，numeric 指定需要转成数值的列。

    注意：不能用「除第一列外全是数值」这种假设——门店表里 store_name、
    store_region 也是文本列，误转会把它们整列变成 NaN。
    """
    path = os.path.join(RAW, '%s.csv' % name)
    df = pd.read_csv(path, header=0, dtype=str, keep_default_na=False)
    df.columns = columns
    for c in numeric:
        df[c] = pd.to_numeric(df[c].replace(NULL_TOKENS, None), errors='coerce')
    return df


def clean_daily():
    d = load('daily_sales', ['dt', 'sales_amt', 'order_cnt', 'sales_qty'],
             ['sales_amt', 'order_cnt', 'sales_qty'])
    d['dt'] = pd.to_datetime(d['dt'], format='%Y%m%d')
    d = d.sort_values('dt').reset_index(drop=True)
    # 按自然日补全：某天没有任何交易时，趋势图上应显示为 0 而不是断档
    full = pd.date_range(d['dt'].min(), d['dt'].max(), freq='D')
    missing_days = len(full) - len(d)
    d = d.set_index('dt').reindex(full).fillna(0).rename_axis('dt').reset_index()
    # IQR 异常值识别
    q1, q3 = d['sales_amt'].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    d['is_outlier'] = (d['sales_amt'] < lo) | (d['sales_amt'] > hi)
    d['avg_order_amt'] = (d['sales_amt'] / d['order_cnt'].replace(0, pd.NA)).round(2)
    d['weekday'] = d['dt'].dt.dayofweek            # 0=周一
    d['is_weekend'] = d['weekday'] >= 5
    return d, missing_days, (lo, hi)


def main():
    daily, missing_days, (lo, hi) = clean_daily()

    region = load('region_sales', ['region', 'total_sales', 'total_qty', 'store_cnt'],
                  ['total_sales', 'total_qty', 'store_cnt'])
    region['store_avg'] = (region['total_sales'] / region['store_cnt']).round(2)

    goods = load('goods_top10', ['goods_name', 'category_name', 'total_sales', 'total_qty'],
                 ['total_sales', 'total_qty'])
    goods['goods_name'] = goods['goods_name'].fillna('未知商品')
    goods['category_name'] = goods['category_name'].fillna('其他')

    store = load('store_top10', ['store_id', 'store_name', 'store_region', 'total_sales', 'total_qty'],
                 ['total_sales', 'total_qty'])
    store['store_name'] = store['store_name'].fillna('未知门店')

    pay = load('pay_type', ['pay_type', 'trade_cnt', 'total_amount'],
               ['trade_cnt', 'total_amount'])
    pay['amount_pct'] = (pay['total_amount'] / pay['total_amount'].sum() * 100).round(2)
    pay['cnt_pct'] = (pay['trade_cnt'] / pay['trade_cnt'].sum() * 100).round(2)

    print('===== 数据清洗结果 =====')
    for df, nm in [(daily, 'daily'), (region, 'region'), (goods, 'goods'),
                   (store, 'store'), (pay, 'pay')]:
        na = int(df.isna().sum().sum())
        print('[OK] %-8s 行数=%-4d 缺失值=%d' % (nm, len(df), na))
    print('')
    print('日销售日期补全：原始 %d 天 -> 补全后 %d 天（补 %d 天）'
          % (len(daily) - missing_days, len(daily), missing_days))
    print('IQR 异常值区间：%.2f ~ %.2f 元，标记异常 %d 天'
          % (lo, hi, int(daily['is_outlier'].sum())))
    print('')
    print('===== 2024年6月经营概览 =====')
    print('总销售额   : %14.2f 元' % daily['sales_amt'].sum())
    print('总订单数   : %14d 单' % int(daily['order_cnt'].sum()))
    print('总销量     : %14d 件' % int(daily['sales_qty'].sum()))
    print('日均销售额 : %14.2f 元' % daily['sales_amt'].mean())
    imax = daily['sales_amt'].idxmax()
    imin = daily['sales_amt'].idxmin()
    print('最高单日   : %s  %10.2f 元' % (daily.loc[imax, 'dt'].date(), daily.loc[imax, 'sales_amt']))
    print('最低单日   : %s  %10.2f 元' % (daily.loc[imin, 'dt'].date(), daily.loc[imin, 'sales_amt']))
    wk = daily.loc[~daily['is_weekend'], 'sales_amt'].mean()
    we = daily.loc[daily['is_weekend'], 'sales_amt'].mean()
    print('工作日日均 : %14.2f 元（%d 天）' % (wk, int((~daily['is_weekend']).sum())))
    print('周末日均   : %14.2f 元（%d 天）' % (we, int(daily['is_weekend'].sum())))
    print('周末/工作日: %14.2f 倍' % (we / wk))
    print('')
    print('===== 门店 TOP10（6月累计）=====')
    for _, r in store.sort_values('total_sales', ascending=False).iterrows():
        print('  %-9s %-14s %-4s %12.2f 元  %5d 件'
              % (r['store_id'], r['store_name'], r['store_region'], r['total_sales'], r['total_qty']))
    print('')
    print('===== 大区汇总 =====')
    for _, r in region.iterrows():
        print('  %-4s 门店%d家  %12.2f 元  %6d 件  单店均值 %10.2f 元'
              % (r['region'], r['store_cnt'], r['total_sales'], r['total_qty'], r['store_avg']))
    print('')
    print('===== 支付方式 =====')
    for _, r in pay.iterrows():
        print('  %-6s %5d 笔（%.1f%%）  %12.2f 元（%.1f%%）'
              % (r['pay_type'], r['trade_cnt'], r['cnt_pct'], r['total_amount'], r['amount_pct']))

    for df, nm in [(daily, 'daily'), (region, 'region'), (goods, 'goods'),
                   (store, 'store'), (pay, 'pay')]:
        df.to_csv(os.path.join(CLEAN, '%s_clean.csv' % nm),
                  index=False, encoding='utf-8-sig')
    print('\n清洗结果已写出到 %s/' % CLEAN)


if __name__ == '__main__':
    main()
