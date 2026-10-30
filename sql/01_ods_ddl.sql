-- =============================================================================
-- 01_ods_ddl.sql —— ODS 贴源层建表
--
-- 定位：ODS 层贴源保存 POS 交易日志与业务库门店维表。
--
-- 重建说明：
--   本脚本按实训环境重建，未在编写环境执行。
--   仓库只保留聚合结果，不含 POS 日志明细；ODS 贴源字段按 DWD 所需的最小
--   字段集重建，字段来源见下方注释；DWD / DWS 的字段名以 data/*.csv 的
--   聚合口径与 dashboard-java 的 DAO 查询为准。
--
-- 采集方式：
--   ods_pos_trade_log   Flume 采集 POS 交易日志，按 dt + store_id 两级分区
--   ods_business_store  Sqoop 从 MySQL 业务库全量同步，门店维表一店一行
--
-- 字段来源：
--   order_id / trade_time / goods_id / goods_name / category_code /
--   quantity / trade_amount / pay_type_code 来自 POS 日志；
--   store_id / store_name / store_region 来自业务库门店表。
--   支付方式编码、品类编码在 DWD 层翻译为中文名称。
--
-- 重建假设（仓库没有明细数据，以下为可执行的参考约定，不是仓库可证事实）：
--   * POS 日志按制表符分隔，目录为 .../dt=YYYYMMDD/store_id=storeXXX；
--   * 支付编码 1/2/3、品类编码 01/02/03 为示例映射；
--   * 残留测试交易以 order_id 的 TEST 前缀标识。
--   若实训环境的实际编码或标记不同，只需替换 DWD 中对应的 CASE WHEN 与过滤条件。
-- =============================================================================

CREATE DATABASE IF NOT EXISTS hui_min_ods;


-- -----------------------------------------------------------------------------
-- 1. POS 交易日志贴源表
--    分区字段：
--      dt       业务日期，格式 yyyyMMdd，取自日志目录 dt=20240601
--      store_id 门店 ID，取自日志目录 store_id=store001
--    一行一条交易明细；同一订单可以包含多条商品明细。
-- -----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS hui_min_ods.ods_pos_trade_log (
    order_id       STRING        COMMENT '订单号；用于明细追溯与残留测试交易过滤',
    trade_time     STRING        COMMENT '交易时间，格式 yyyy-MM-dd HH:mm:ss；同一订单的多条商品明细共享同一时间点',
    goods_id       STRING        COMMENT '商品编码',
    goods_name     STRING        COMMENT '商品名称（POS 日志冗余字段）',
    category_code  STRING        COMMENT '品类编码：01 生鲜 / 02 日用品 / 03 家电',
    quantity       INT           COMMENT '购买件数',
    trade_amount   DECIMAL(12,2) COMMENT '明细成交金额（元）',
    pay_type_code  STRING        COMMENT '支付方式编码：1 现金 / 2 支付宝 / 3 微信支付'
)
COMMENT 'ODS：POS 交易日志贴源表，按业务日期 + 门店两级分区'
PARTITIONED BY (dt STRING, store_id STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/origin_data/retail/ods_pos_trade_log';


-- -----------------------------------------------------------------------------
-- 2. 业务库门店维表
--    Sqoop 全量同步，保持一店一行；只保留 DWD 关联所需字段。
-- -----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS hui_min_ods.ods_business_store (
    store_id      STRING COMMENT '门店 ID，主键',
    store_name    STRING COMMENT '门店名称',
    store_region  STRING COMMENT '所属大区：华北 / 华东 / 华南'
)
COMMENT 'ODS：MySQL 业务库门店维表，Sqoop 全量同步'
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/origin_data/retail/ods_business_store';


-- Flume 按 dt=.../store_id=... 建目录后，刷新分区元数据。
-- 业务库门店表为全量覆盖，不需要分区修复。
MSCK REPAIR TABLE hui_min_ods.ods_pos_trade_log;
