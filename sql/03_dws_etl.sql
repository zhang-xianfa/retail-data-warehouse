-- =============================================================================
-- 03_dws_etl.sql —— DWS 门店日销汇总
--
-- 目标表：hui_min_dws.dws_store_sales_daily
-- 粒度：一个门店一个业务日一行（整月口径下 30 天 × 10 门店 = 300 行）
-- 指标：销售额 / 销量 / 订单数 / 客单价
-- 写法：INSERT OVERWRITE + 动态分区，一条作业写出整月 30 个 dt 分区。
--
-- 重建说明：
--   本脚本按实训环境重建，字段以仓库 data/*.csv 与 dashboard-java 的 DAO
--   查询为准，未在编写环境执行。
-- 字段对齐：
--   store_id / store_name / store_region / sales_amount / sales_quantity /
--   order_cnt / avg_order_amount / dt 与 StoreSalesDAO 的查询字段一致。
-- =============================================================================

CREATE DATABASE IF NOT EXISTS hui_min_dws;


-- -----------------------------------------------------------------------------
-- 目标表：门店日销汇总表
-- 客单价 = 销售额 / 订单数（按门店日口径），与 analysis/data_clean.py 中
-- avg_order_amt = sales_amt / order_cnt 的口径一致。
-- 订单数口径与 StoreSalesVO 注释一致：按去重交易时间点数统计；
-- 同一订单的多条商品明细共享同一 trade_time。
-- 若实训环境的 POS 日志以 order_id 作为订单唯一标识，可将下方
-- trade_time 改为 order_id；本仓库现有注释采用的是交易时间点口径。
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hui_min_dws.dws_store_sales_daily (
    store_id          STRING        COMMENT '门店 ID',
    store_name        STRING        COMMENT '门店名称',
    store_region      STRING        COMMENT '所属大区',
    sales_amount      DECIMAL(14,2) COMMENT '销售额（元）',
    sales_quantity    INT           COMMENT '销量（件）',
    order_cnt         INT           COMMENT '订单数（去重交易时间点数）',
    avg_order_amount  DECIMAL(12,2) COMMENT '客单价（元）= 销售额 / 订单数'
)
COMMENT 'DWS：门店日销汇总表'
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');


-- -----------------------------------------------------------------------------
-- 动态分区参数：
--   mode=nonstrict 允许不指定静态分区值；
--   max.dynamic.partitions 控制单作业可写分区总数，避免分区过多时报错。
-- 分区列 dt 必须是 SELECT 的最后一列。
-- -----------------------------------------------------------------------------
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.max.dynamic.partitions=1000;
SET hive.exec.max.dynamic.partitions.pernode=100;
SET hive.exec.max.created.files=100000;
-- Spark 侧动态分区覆盖，避免 INSERT OVERWRITE 误删未写入的分区；
-- Hive 执行时该参数不生效，仅作为会话变量存在。
SET spark.sql.sources.partitionOverwriteMode=dynamic;

INSERT OVERWRITE TABLE hui_min_dws.dws_store_sales_daily PARTITION (dt)
SELECT
    store_id,
    max(store_name)                                       AS store_name,
    max(store_region)                                     AS store_region,
    cast(round(sum(trade_amount), 2) AS DECIMAL(14,2))    AS sales_amount,
    cast(sum(trade_quantity) AS INT)                      AS sales_quantity,
    cast(count(DISTINCT trade_time) AS INT)               AS order_cnt,
    cast(round(sum(trade_amount) / count(DISTINCT trade_time), 2)
         AS DECIMAL(12,2))                                AS avg_order_amount,
    dt
FROM hui_min_dwd.dwd_trade_detail
WHERE dt BETWEEN '20240601' AND '20240630'
GROUP BY dt, store_id;
