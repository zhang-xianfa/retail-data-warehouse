-- =============================================================================
-- 04_quality_reconcile.sql —— 三层对账与数据质量检查
--
-- 对账口径（README）：
--   ODS / DWD / DWS 三层行数、金额合计、维度基数一致；
--   残留测试交易 0 条、未匹配门店 0 条。
--
-- 结果解读：
--   ods_dwd_diff / dwd_dws_diff 为相邻层差异，全部为 0 即通过；
--   check_result 列直接给出 PASS / FAIL。
--
-- 重建说明：
--   本脚本按实训环境重建，字段以仓库 data/*.csv 与 dashboard-java 的 DAO
--   查询为准，未在编写环境执行。
-- 基准值仅用于说明（来自 README）：4972 笔有效交易、4166 单、
--   400,606.67 元、300 个 ODS 分区；脚本本身不写死这些值，只做层间比较。
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 对账 1/3：行数
--   交易明细行数：ODS 有效行 vs DWD 行数
--   有效订单数  ：ODS / DWD 按 dt + store_id + trade_time 去重 vs DWS 的 order_cnt 合计
--   销量（件）  ：ODS quantity 合计 vs DWD trade_quantity 合计 vs DWS 合计
--   门店日行数  ：ODS / DWD 的 dt + store_id 基数 vs DWS 行数
-- -----------------------------------------------------------------------------
WITH ods AS (
    SELECT count(*)                                      AS row_cnt,
           count(DISTINCT concat_ws('_', dt, store_id, trade_time)) AS order_cnt,
           sum(quantity)                                 AS qty_cnt,
           count(DISTINCT concat_ws('_', dt, store_id))  AS store_day_cnt
    FROM hui_min_ods.ods_pos_trade_log
    WHERE dt BETWEEN '20240601' AND '20240630'
      AND order_id IS NOT NULL
      AND trim(order_id) <> ''
      AND trade_time IS NOT NULL
      AND trim(trade_time) <> ''
      AND upper(trim(order_id)) NOT LIKE 'TEST%'
      AND trade_amount IS NOT NULL
      AND trade_amount > 0
      AND quantity IS NOT NULL
      AND quantity > 0
      AND store_id IS NOT NULL
      AND store_id <> '__HIVE_DEFAULT_PARTITION__'
),
dwd AS (
    SELECT count(*)                                      AS row_cnt,
           count(DISTINCT concat_ws('_', dt, store_id, trade_time)) AS order_cnt,
           sum(trade_quantity)                           AS qty_cnt,
           count(DISTINCT concat_ws('_', dt, store_id))  AS store_day_cnt
    FROM hui_min_dwd.dwd_trade_detail
    WHERE dt BETWEEN '20240601' AND '20240630'
),
dws AS (
    SELECT count(*)                                      AS row_cnt,
           sum(order_cnt)                                AS order_cnt,
           sum(sales_quantity)                           AS qty_cnt,
           count(DISTINCT concat_ws('_', dt, store_id))  AS store_day_cnt
    FROM hui_min_dws.dws_store_sales_daily
    WHERE dt BETWEEN '20240601' AND '20240630'
)
SELECT metric,
       ods_value,
       dwd_value,
       dws_value,
       ods_dwd_diff,
       dwd_dws_diff,
       CASE WHEN coalesce(ods_dwd_diff, 0) = 0
             AND coalesce(dwd_dws_diff, 0) = 0
            THEN 'PASS' ELSE 'FAIL' END AS check_result
FROM (
    SELECT '交易明细行数' AS metric,
           ods.row_cnt    AS ods_value,
           dwd.row_cnt    AS dwd_value,
           cast(NULL AS BIGINT) AS dws_value,
           dwd.row_cnt - ods.row_cnt AS ods_dwd_diff,
           cast(NULL AS BIGINT)      AS dwd_dws_diff
    FROM ods CROSS JOIN dwd

    UNION ALL

    SELECT '有效订单数',
           ods.order_cnt,
           dwd.order_cnt,
           dws.order_cnt,
           dwd.order_cnt - ods.order_cnt,
           dws.order_cnt - dwd.order_cnt
    FROM ods CROSS JOIN dwd CROSS JOIN dws

    UNION ALL

    SELECT '销量（件）',
           ods.qty_cnt,
           dwd.qty_cnt,
           dws.qty_cnt,
           dwd.qty_cnt - ods.qty_cnt,
           dws.qty_cnt - dwd.qty_cnt
    FROM ods CROSS JOIN dwd CROSS JOIN dws

    UNION ALL

    SELECT '门店日汇总行数',
           ods.store_day_cnt,
           dwd.store_day_cnt,
           dws.row_cnt,
           dwd.store_day_cnt - ods.store_day_cnt,
           dws.row_cnt - dwd.store_day_cnt
    FROM ods CROSS JOIN dwd CROSS JOIN dws
) t
ORDER BY metric;


-- -----------------------------------------------------------------------------
-- 对账 2/3：金额合计
-- -----------------------------------------------------------------------------
WITH ods AS (
    SELECT round(sum(trade_amount), 2) AS amt
    FROM hui_min_ods.ods_pos_trade_log
    WHERE dt BETWEEN '20240601' AND '20240630'
      AND order_id IS NOT NULL
      AND trim(order_id) <> ''
      AND trade_time IS NOT NULL
      AND trim(trade_time) <> ''
      AND upper(trim(order_id)) NOT LIKE 'TEST%'
      AND trade_amount IS NOT NULL
      AND trade_amount > 0
      AND quantity IS NOT NULL
      AND quantity > 0
      AND store_id IS NOT NULL
      AND store_id <> '__HIVE_DEFAULT_PARTITION__'
),
dwd AS (
    SELECT round(sum(trade_amount), 2) AS amt
    FROM hui_min_dwd.dwd_trade_detail
    WHERE dt BETWEEN '20240601' AND '20240630'
),
dws AS (
    SELECT round(sum(sales_amount), 2) AS amt
    FROM hui_min_dws.dws_store_sales_daily
    WHERE dt BETWEEN '20240601' AND '20240630'
)
SELECT '销售金额合计（元）' AS metric,
       ods.amt AS ods_value,
       dwd.amt AS dwd_value,
       dws.amt AS dws_value,
       cast(dwd.amt - ods.amt AS DECIMAL(18,2)) AS ods_dwd_diff,
       cast(dws.amt - dwd.amt AS DECIMAL(18,2)) AS dwd_dws_diff,
       CASE WHEN coalesce(dwd.amt - ods.amt, 0) = 0
             AND coalesce(dws.amt - dwd.amt, 0) = 0
            THEN 'PASS' ELSE 'FAIL' END AS check_result
FROM ods CROSS JOIN dwd CROSS JOIN dws;


-- -----------------------------------------------------------------------------
-- 对账 2/3 补充：门店日粒度金额差异
--   按 dt + store_id 全外连接，金额不一致或单边缺失都应返回 0 行。
-- -----------------------------------------------------------------------------
SELECT '门店日金额不一致行数' AS metric,
       count(*) AS diff_rows,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS check_result
FROM (
    SELECT coalesce(d.dt, w.dt)             AS dt,
           coalesce(d.store_id, w.store_id) AS store_id,
           d.amt                            AS dwd_amt,
           w.sales_amount                   AS dws_amt
    FROM (
        SELECT dt,
               store_id,
               round(sum(trade_amount), 2) AS amt
        FROM hui_min_dwd.dwd_trade_detail
        WHERE dt BETWEEN '20240601' AND '20240630'
        GROUP BY dt, store_id
    ) d
    FULL OUTER JOIN hui_min_dws.dws_store_sales_daily w
      ON d.dt = w.dt
     AND d.store_id = w.store_id
    WHERE d.amt IS NULL
       OR w.sales_amount IS NULL
       OR d.amt <> w.sales_amount
) t;


-- -----------------------------------------------------------------------------
-- 对账 3/3：维度基数
--   门店数 / 业务日期数：三层对比；商品数：ODS 与 DWD 对比。
-- -----------------------------------------------------------------------------
WITH ods AS (
    SELECT count(DISTINCT store_id) AS store_cnt,
           count(DISTINCT dt)       AS dt_cnt,
           count(DISTINCT goods_id) AS goods_cnt
    FROM hui_min_ods.ods_pos_trade_log
    WHERE dt BETWEEN '20240601' AND '20240630'
      AND order_id IS NOT NULL
      AND trim(order_id) <> ''
      AND trade_time IS NOT NULL
      AND trim(trade_time) <> ''
      AND upper(trim(order_id)) NOT LIKE 'TEST%'
      AND trade_amount IS NOT NULL
      AND trade_amount > 0
      AND quantity IS NOT NULL
      AND quantity > 0
      AND store_id IS NOT NULL
      AND store_id <> '__HIVE_DEFAULT_PARTITION__'
),
dwd AS (
    SELECT count(DISTINCT store_id) AS store_cnt,
           count(DISTINCT dt)       AS dt_cnt,
           count(DISTINCT goods_id) AS goods_cnt
    FROM hui_min_dwd.dwd_trade_detail
    WHERE dt BETWEEN '20240601' AND '20240630'
),
dws AS (
    SELECT count(DISTINCT store_id) AS store_cnt,
           count(DISTINCT dt)       AS dt_cnt,
           cast(NULL AS BIGINT)     AS goods_cnt
    FROM hui_min_dws.dws_store_sales_daily
    WHERE dt BETWEEN '20240601' AND '20240630'
)
SELECT metric,
       ods_value,
       dwd_value,
       dws_value,
       ods_dwd_diff,
       dwd_dws_diff,
       CASE WHEN coalesce(ods_dwd_diff, 0) = 0
             AND coalesce(dwd_dws_diff, 0) = 0
            THEN 'PASS' ELSE 'FAIL' END AS check_result
FROM (
    SELECT '门店数' AS metric,
           ods.store_cnt,
           dwd.store_cnt,
           dws.store_cnt,
           dwd.store_cnt - ods.store_cnt,
           dws.store_cnt - dwd.store_cnt
    FROM ods CROSS JOIN dwd CROSS JOIN dws

    UNION ALL

    SELECT '业务日期数',
           ods.dt_cnt,
           dwd.dt_cnt,
           dws.dt_cnt,
           dwd.dt_cnt - ods.dt_cnt,
           dws.dt_cnt - dwd.dt_cnt
    FROM ods CROSS JOIN dwd CROSS JOIN dws

    UNION ALL

    SELECT '商品数',
           ods.goods_cnt,
           dwd.goods_cnt,
           cast(NULL AS BIGINT),
           dwd.goods_cnt - ods.goods_cnt,
           cast(NULL AS BIGINT)
    FROM ods CROSS JOIN dwd
) t
ORDER BY metric;


-- -----------------------------------------------------------------------------
-- 附加检查 1：残留测试交易
--   ODS 中可能仍有 TEST 前缀交易；DWD 过滤后应为 0 条。
-- -----------------------------------------------------------------------------
WITH ods_test AS (
    SELECT count(*) AS cnt
    FROM hui_min_ods.ods_pos_trade_log
    WHERE dt BETWEEN '20240601' AND '20240630'
      AND upper(trim(order_id)) LIKE 'TEST%'
),
dwd_test AS (
    SELECT count(*) AS cnt
    FROM hui_min_dwd.dwd_trade_detail
    WHERE dt BETWEEN '20240601' AND '20240630'
      AND upper(trim(order_id)) LIKE 'TEST%'
)
SELECT '残留测试交易' AS metric,
       ods_test.cnt AS ods_test_rows,
       dwd_test.cnt AS dwd_test_rows,
       cast(0 AS BIGINT) AS expected_rows,
       CASE WHEN dwd_test.cnt = 0 THEN 'PASS' ELSE 'FAIL' END AS check_result
FROM ods_test CROSS JOIN dwd_test;


-- -----------------------------------------------------------------------------
-- 附加检查 2：未匹配门店
--   ODS 中门店 ID 在维表找不到、DWD 出现“未知门店”、DWS 出现“未知门店”
--   都应返回 0 条。
-- -----------------------------------------------------------------------------
WITH ods_unmatched AS (
    SELECT count(*) AS cnt
    FROM hui_min_ods.ods_pos_trade_log l
    LEFT JOIN hui_min_ods.ods_business_store s
           ON l.store_id = s.store_id
    WHERE l.dt BETWEEN '20240601' AND '20240630'
      AND l.store_id IS NOT NULL
      AND l.store_id <> '__HIVE_DEFAULT_PARTITION__'
      AND l.order_id IS NOT NULL
      AND trim(l.order_id) <> ''
      AND l.trade_time IS NOT NULL
      AND trim(l.trade_time) <> ''
      AND upper(trim(l.order_id)) NOT LIKE 'TEST%'
      AND l.trade_amount IS NOT NULL
      AND l.trade_amount > 0
      AND l.quantity IS NOT NULL
      AND l.quantity > 0
      AND s.store_id IS NULL
),
dwd_unmatched AS (
    SELECT count(*) AS cnt
    FROM hui_min_dwd.dwd_trade_detail d
    LEFT JOIN hui_min_ods.ods_business_store s
           ON d.store_id = s.store_id
    WHERE d.dt BETWEEN '20240601' AND '20240630'
      AND (s.store_id IS NULL OR d.store_name = '未知门店')
),
dws_unmatched AS (
    SELECT count(*) AS cnt
    FROM hui_min_dws.dws_store_sales_daily
    WHERE dt BETWEEN '20240601' AND '20240630'
      AND store_name = '未知门店'
)
SELECT '未匹配门店' AS metric,
       ods_unmatched.cnt AS ods_unmatched_rows,
       dwd_unmatched.cnt AS dwd_unmatched_rows,
       dws_unmatched.cnt AS dws_unmatched_rows,
       CASE WHEN ods_unmatched.cnt = 0
             AND dwd_unmatched.cnt = 0
             AND dws_unmatched.cnt = 0
            THEN 'PASS' ELSE 'FAIL' END AS check_result
FROM ods_unmatched CROSS JOIN dwd_unmatched CROSS JOIN dws_unmatched;
