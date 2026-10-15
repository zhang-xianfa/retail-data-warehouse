# -*- coding: utf-8 -*-
"""
retail_dashboard.py —— 惠民零售集团经营数据看板（Streamlit）。

启动：streamlit run retail_dashboard.py --server.port 8501
数据来源：clean/ 目录下由 data_clean.py 产出的 5 份清洗结果。
"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from common import *          # noqa: F401,F403  —— 中文字体与配色

st.set_page_config(page_title='惠民零售集团经营数据看板',
                   page_icon='📊', layout='wide')


@st.cache_data                        # 缓存读盘结果，避免每次交互重复读文件
def load_all():
    d = {}
    for k in ['daily', 'region', 'goods', 'store', 'pay']:
        d[k] = pd.read_csv('clean/%s_clean.csv' % k,
                           parse_dates=['dt'] if k == 'daily' else None)
    return d


data = load_all()
daily = data['daily']

st.title('📊 惠民零售集团 · 经营数据可视化看板')
st.caption('数据链路：POS日志 + MySQL业务库 → Flume/Sqoop → Hive ODS → DWD → DWS → CSV → pandas → Streamlit'
           '　｜　分析周期：2024-06-01 ~ 2024-06-30')

# ---------------------------- 侧边栏筛选 ----------------------------
with st.sidebar:
    st.header('筛选条件')
    d0, d1 = st.date_input(
        '日期区间',
        value=(daily['dt'].min().date(), daily['dt'].max().date()),
        min_value=daily['dt'].min().date(), max_value=daily['dt'].max().date())
    metric = st.selectbox('趋势指标', ['销售额', '订单数', '销量'])
    only_weekend = st.checkbox('仅看周末', value=False)
    st.markdown('---')
    st.write('数据行数：%d 天' % len(daily))
    st.write('数据来源：hui_min_dws.dws_store_sales_daily')

mask = (daily['dt'] >= pd.Timestamp(d0)) & (daily['dt'] <= pd.Timestamp(d1))
if only_weekend:
    mask &= daily['is_weekend']
view = daily[mask]

# ---------------------------- 核心指标卡 ----------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric('总销售额（元）', '{:,.2f}'.format(view['sales_amt'].sum()))
c2.metric('总订单数（单）', '{:,}'.format(int(view['order_cnt'].sum())))
c3.metric('总销量（件）', '{:,}'.format(int(view['sales_qty'].sum())))
c4.metric('日均销售额（元）', '{:,.2f}'.format(view['sales_amt'].mean() if len(view) else 0))
c5.metric('平均客单价（元）',
          '{:,.2f}'.format(view['sales_amt'].sum() / view['order_cnt'].sum()
                           if view['order_cnt'].sum() else 0))

st.markdown('---')

# ---------------------------- ① 日销售趋势 ----------------------------
st.subheader('① 日销售额与订单趋势')
col = {'销售额': 'sales_amt', '订单数': 'order_cnt', '销量': 'sales_qty'}[metric]
fig, ax1 = plt.subplots(figsize=(13, 4))
ax1.plot(view['dt'], view[col], marker='o', color='#2f7ed8', linewidth=2, label=metric)
if len(view):
    ax1.axhline(view[col].mean(), color='#e74c3c', linestyle='--',
                linewidth=1.2, label='区间均值 %.1f' % view[col].mean())
    we = view[view['is_weekend']]
    ax1.scatter(we['dt'], we[col], s=90, facecolors='none',
                edgecolors='#e67e22', linewidths=1.8, label='周末')
ax1.set_xlabel('日期')
ax1.set_ylabel(metric)
ax1.legend(loc='lower right', ncol=3)
ax1.grid(axis='y', linestyle=':', alpha=.45)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# ---------------------------- ②③④⑤ 两列布局 ----------------------------
left, right = st.columns(2)

with left:
    st.subheader('② 各大区销售额对比')
    fig, ax = plt.subplots(figsize=(6, 3.8))
    bars = ax.bar(data['region']['region'], data['region']['total_sales'],
                  color=COLORS[:len(data['region'])], width=0.55)
    for b, v in zip(bars, data['region']['total_sales']):
        ax.text(b.get_x() + b.get_width() / 2, v, '%.0f' % v,
                ha='center', va='bottom', fontsize=9)
    ax.set_ylabel('销售额（元）')
    ax.set_ylim(0, data['region']['total_sales'].max() * 1.2)
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader('④ 门店销售额 TOP10')
    s = data['store'].sort_values('total_sales', ascending=True).tail(10)
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.barh(s['store_name'], s['total_sales'], color='#41b06e', height=0.6)
    ax.set_xlabel('销售额（元）')
    ax.tick_params(axis='y', labelsize=8)
    plt.tight_layout()
    st.pyplot(fig)

with right:
    st.subheader('③ 商品销售额 TOP10')
    g = data['goods'].sort_values('total_sales', ascending=True).tail(10)
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.barh(g['goods_name'], g['total_sales'],
            color=[CAT_COLORS.get(c, '#95a5a6') for c in g['category_name']], height=0.6)
    ax.set_xlabel('销售额（元）')
    ax.tick_params(axis='y', labelsize=8)
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader('⑤ 支付方式金额占比')
    fig, ax = plt.subplots(figsize=(6, 3.8))
    wedges, _t, autot = ax.pie(
        data['pay']['total_amount'], labels=data['pay']['pay_type'],
        colors=COLORS[:len(data['pay'])], autopct='%1.2f%%', startangle=90,
        counterclock=False, wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2))
    for t in autot:
        t.set_fontsize(9)
    plt.tight_layout()
    st.pyplot(fig)

# ---------------------------- 明细数据 ----------------------------
st.subheader('⑥ 明细数据')
t1, t2, t3, t4 = st.tabs(['日销售明细', '商品TOP10', '门店TOP10', '支付方式'])
t1.dataframe(view, use_container_width=True)
t2.dataframe(data['goods'], use_container_width=True)
t3.dataframe(data['store'], use_container_width=True)
t4.dataframe(data['pay'], use_container_width=True)

st.caption('© 2024 惠民零售集团数据看板 ｜ 数据经 Hive 数仓加工后导出，由 pandas 清洗、Streamlit 呈现')
