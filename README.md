# 零售数仓分层构建与可视化分析

> Hadoop / Hive / Spark SQL 离线数仓 ＋ Python 分析层 ＋ Spring Boot + ECharts 看板

以零售集团「POS 交易日志 ＋ 业务库」为数据源，搭建 **ODS → DWD → DWS** 三层离线数仓，
并在上层完成经营分析与可视化。

---

## 一、数仓分层

| 层 | 做什么 | 技术 |
|---|---|---|
| **ODS** 贴源层 | 采集 POS 交易日志、同步 MySQL 业务库 | `Flume` 采集日志、`Sqoop` 全量 / 按时间戳增量同步；落地 HDFS，按**业务日期 + 门店**两级分区 |
| **DWD** 明细层 | 多表关联、编码翻译、缺失值填充，生成明细宽表 | `Spark SQL` |
| **DWS** 汇总层 | 门店日销汇总（销售额 / 销量 / 订单数 / 客单价） | `Spark SQL`，**动态分区**一次作业写出整月 30 个分区 |

**数据规模**：整月 30 天 × 10 门店 = **300 个日志文件**、**4972 笔**有效交易、
ODS 分区总数 **300**、总销售额 **400,606.67 元**、总订单 4166 单。

## 二、数据质量与性能优化

- **三层逐层对账**（行数、金额合计、维度基数）：ODS / DWD / DWS 三层金额合计
  **完全一致（0 差异）**，并校验残留测试交易 0 条、未匹配门店 0 条
- **性能优化**：定位到 HiveServer2 查询瓶颈后，开启 `hive.exec.mode.local.auto`
  以规避小数据量下的作业调度开销，接口响应由 **57.2 s 降到 1.6 ~ 3.2 s（约 30 倍）**

## 三、经营分析结论（部分）

| 维度 | 结论 |
|---|---|
| 周末效应 | 周末日均 **17,963 元** vs 工作日 **11,049 元**，达 **1.63 倍** |
| 品类 | 家电贡献 **73.1%** 销售额（914 笔 / 292,946 元） |
| 门店 | store001 单店 **97,087.77 元**，占全区 24.2%，超过整个华南区 |
| 支付 | 现金 / 支付宝 / 微信 各约 **1/3** |
| 价格 | IQR 异常区间 2,881.94 ~ 23,861.47 元，标记异常 **0 天** |

## 四、本仓库内容

```
analysis/                    Python 分析层
  data_clean.py              数据清洗（缺失值、日期补全、IQR 异常值识别）
  chart1_trend.py ~ chart7_avgorder.py   7 张分析图表（日销趋势 / 大区 / 商品 / 门店 / 支付 / 周末 / 客单价）
  retail_dashboard.py        Streamlit 交互看板
  charts/                    产出的 7 张图表
data/                        教学用模拟数据的聚合结果（日销 / 大区 / 商品 TOP10 / 门店 TOP10 / 支付）
dashboard-java/              Spring Boot + ECharts 看板
  src/main/java/.../dao/StoreSalesDAO.java    Hive SQL 查询（JDBC 直连 HiveServer2）
  src/main/java/.../controller/AnalysisController.java  7 个分析接口
  src/main/resources/static/                  ECharts 页面
```

**Java 看板接口**：`/api/retail/store/salesTop10`、`/region/sales`、`/category/share`、
`/goods/top10`、`/pay/dist`、`/dates`、`/health`

## 五、运行

```bash
# Python 分析层
pip install pandas matplotlib streamlit
python analysis/data_clean.py
python analysis/chart1_trend.py        # 依次执行 chart1 ~ chart7
streamlit run analysis/retail_dashboard.py

# Java 看板（需可用的 HiveServer2，连接串见 application.yml）
cd dashboard-java && mvn spring-boot:run
```

---

## 说明

- 数据为课程实训用**模拟数据**（由本人编写的数据生成脚本按规则产出），**不含真实客户信息**；
  仓库中只保留聚合结果，未包含任何明细数据。
- 数仓的 Hive / Spark SQL 脚本属于实训实验内容，未包含在本仓库中——
  本仓库是其上的**分析层与可视化层**。
