-- =============================================================================
-- 02_dwd_etl.sql —— DWD 明细层 ETL
--
-- 目标表：hui_min_dwd.dwd_trade_detail
-- 粒度：一行一条 POS 交易明细（与 StoreSalesDAO 中 count(*) / sum(trade_*) 口径一致）
--
-- 处理链路：
--   1) POS 日志 LEFT JOIN 门店维表，补齐 store_name / store_region；
--   2) 支付方式、品类编码用 CASE WHEN 翻译为中文名称；
--   3) 文本缺失填充：门店名 -> 未知门店，商品名 -> 未知商品，品类 -> 其他；
--   4) 按 01 的重建假设过滤残留测试交易（order_id 以 TEST 开头）与金额 / 数量非正的脏数据。
--
-- 重建说明：
--   本脚本按实训环境重建，未在编写环境执行；DWD 目标字段与 dashboard-java
--   的 DAO 查询字段对齐，ODS 贴源字段按 POS 日志最小字段集重建。
-- 字段对齐：
--   trade_amount / trade_quantity / pay_type / goods_name / category_name / dt
--   与 StoreSalesDAO 中 dwd_trade_detail 的查询字段一致。
-- =============================================================================

CREATE DATABASE IF NOT EXISTS hui_min_dwd;


-- -----------------------------------------------------------------------------
-- 目标表：DWD 交易明细宽表
-- 说明：关键字段缺失的交易无法参与订单数 / 销售额对账，在 ETL 中直接过滤，
--       不补 0，避免把脏数据带进 DWS。
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hui_min_dwd.dwd_trade_detail (
    order_id        STRING        COMMENT '订单号',
    trade_time      STRING        COMMENT '交易时间；同一订单的多条商品明细共享同一时间点',
    store_id        STRING        COMMENT '门店 ID',
    store_name      STRING        COMMENT '门店名称（缺失填充为“未知门店”）',
    store_region    STRING        COMMENT '所属大区',
    goods_id        STRING        COMMENT '商品编码',
    goods_name      STRING        COMMENT '商品名称（缺失填充为“未知商品”）',
    category_code   STRING        COMMENT '品类编码（保留原编码便于追溯）',
    category_name   STRING        COMMENT '品类名称（编码翻译，未知归入“其他”）',
    trade_quantity  INT           COMMENT '销量（件）',
    trade_amount    DECIMAL(12,2) COMMENT '成交金额（元）',
    pay_type_code   STRING        COMMENT '支付方式编码',
    pay_type        STRING        COMMENT '支付方式名称（编码翻译）'
)
COMMENT 'DWD：交易明细宽表'
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');


-- -----------------------------------------------------------------------------
-- ETL：动态分区写入
-- Hive 会话参数；spark-sql 下同样可执行，Spark 需开启 Hive 支持。
-- -----------------------------------------------------------------------------
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.max.dynamic.partitions=1000;
SET hive.exec.max.dynamic.partitions.pernode=100;
-- Spark 侧动态分区覆盖，避免 INSERT OVERWRITE 误删未写入的分区；
-- Hive 执行时该参数不生效，仅作为会话变量存在。
SET spark.sql.sources.partitionOverwriteMode=dynamic;

INSERT OVERWRITE TABLE hui_min_dwd.dwd_trade_detail PARTITION (dt)
SELECT
    l.order_id,
    l.trade_time,
    l.store_id,
    coalesce(nullif(trim(s.store_name), ''), '未知门店')  AS store_name,
    s.store_region,
    l.goods_id,
    coalesce(nullif(trim(l.goods_name), ''), '未知商品')  AS goods_name,
    l.category_code,
    CASE l.category_code
        WHEN '01' THEN '生鲜'
        WHEN '02' THEN '日用品'
        WHEN '03' THEN '家电'
        ELSE '其他'
    END                                                   AS category_name,
    l.quantity                                            AS trade_quantity,
    l.trade_amount,
    l.pay_type_code,
    CASE l.pay_type_code
        WHEN '1' THEN '现金'
        WHEN '2' THEN '支付宝'
        WHEN '3' THEN '微信支付'
        ELSE '其他'
    END                                                   AS pay_type,
    l.dt
FROM hui_min_ods.ods_pos_trade_log l
LEFT JOIN hui_min_ods.ods_business_store s
       ON l.store_id = s.store_id
WHERE l.dt BETWEEN '20240601' AND '20240630'
  -- 关键字段缺失直接过滤，避免污染订单数与销售额
  AND l.order_id IS NOT NULL
  AND trim(l.order_id) <> ''
  AND l.trade_time IS NOT NULL
  AND trim(l.trade_time) <> ''
  -- 按 01 的重建假设：残留测试交易订单号以 TEST 开头
  AND upper(trim(l.order_id)) NOT LIKE 'TEST%'
  AND l.trade_amount IS NOT NULL
  AND l.trade_amount > 0
  AND l.quantity IS NOT NULL
  AND l.quantity > 0
  -- 门店分区缺失时 Hive 会落到默认分区，一并排除
  AND l.store_id IS NOT NULL
  AND l.store_id <> '__HIVE_DEFAULT_PARTITION__';
