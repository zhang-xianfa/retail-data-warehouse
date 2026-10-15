package com.huimin.retail.dao;

import com.huimin.retail.vo.CategoryShareVO;
import com.huimin.retail.vo.StoreSalesVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.BeanPropertyRowMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;

/**
 * 数据访问层：使用 JdbcTemplate 访问 Hive 数仓。
 * <p>
 * 使用 JdbcTemplate 而非 JPA 的原因：Hive SQL 的方言（分区、窗口函数、复杂类型）
 * 与 MySQL 差异较大，JPA 自动生成的 SQL 容易出错；JdbcTemplate 保留 SQL 的全部控制力，
 * 同时免去原生 JDBC 的样板代码。BeanPropertyRowMapper 按「列别名 = Java 属性名」自动映射。
 */
@Repository
public class StoreSalesDAO {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 查询某天指定大区的门店销售额 TOP N。
     *
     * @param dt     业务日期，格式 yyyyMMdd
     * @param region 大区，null 或 "all" 表示不限制
     * @param topN   取前 N 条
     */
    public List<StoreSalesVO> queryStoreSalesTopN(String dt, String region, int topN) {
        StringBuilder sql = new StringBuilder()
                .append("select store_id              as storeId, ")
                .append("       store_name            as storeName, ")
                .append("       store_region          as storeRegion, ")
                .append("       sales_amount          as salesAmount, ")
                .append("       sales_quantity        as salesQuantity, ")
                .append("       order_cnt             as orderCnt, ")
                .append("       avg_order_amount      as avgOrderAmount ")
                .append("  from dws_store_sales_daily ")
                .append(" where dt = ? ");

        List<Object> params = new ArrayList<>();
        params.add(dt);

        // 大区为可选筛选条件，参数通过占位符绑定，防止 SQL 注入
        if (region != null && !region.trim().isEmpty() && !"all".equalsIgnoreCase(region)) {
            sql.append(" and store_region = ? ");
            params.add(region);
        }
        sql.append(" order by sales_amount desc limit ").append(topN);

        return jdbcTemplate.query(sql.toString(), params.toArray(),
                new BeanPropertyRowMapper<>(StoreSalesVO.class));
    }

    /**
     * 查询某天各大区的汇总数据（用于区域对比图）。
     */
    public List<StoreSalesVO> queryRegionSummary(String dt) {
        String sql = "select store_region        as storeRegion, "
                + "       round(sum(sales_amount),2)  as salesAmount, "
                + "       sum(sales_quantity)         as salesQuantity, "
                + "       sum(order_cnt)              as orderCnt "
                + "  from dws_store_sales_daily "
                + " where dt = ? "
                + " group by store_region "
                + " order by salesAmount desc";
        return jdbcTemplate.query(sql, new Object[]{dt},
                new BeanPropertyRowMapper<>(StoreSalesVO.class));
    }

    /**
     * 查询某天各商品品类的销售额与销量（用于品类占比饼图）。
     */
    public List<CategoryShareVO> queryCategoryShare(String dt) {
        String sql = "select category_name                 as categoryName, "
                + "       round(sum(trade_amount),2)    as salesAmount, "
                + "       sum(trade_quantity)           as salesQuantity, "
                + "       count(*)                      as tradeCnt "
                + "  from hui_min_dwd.dwd_trade_detail "
                + " where dt = ? "
                + " group by category_name "
                + " order by salesAmount desc";
        return jdbcTemplate.query(sql, new Object[]{dt},
                new BeanPropertyRowMapper<>(CategoryShareVO.class));
    }

    /**
     * 查询某天销售额 TOP N 的商品（用于商品热销分析）。
     */
    public List<CategoryShareVO> queryGoodsTopN(String dt, int topN) {
        String sql = "select concat(goods_name, ' (', category_name, ')')  as categoryName, "
                + "       round(sum(trade_amount),2)    as salesAmount, "
                + "       sum(trade_quantity)           as salesQuantity, "
                + "       count(*)                      as tradeCnt "
                + "  from hui_min_dwd.dwd_trade_detail "
                + " where dt = ? "
                + " group by goods_name, category_name "
                + " order by salesAmount desc limit " + topN;
        return jdbcTemplate.query(sql, new Object[]{dt},
                new BeanPropertyRowMapper<>(CategoryShareVO.class));
    }

    /**
     * 查询某天各支付方式的交易分布。
     */
    public List<CategoryShareVO> queryPayTypeDist(String dt) {
        String sql = "select pay_type                     as categoryName, "
                + "       round(sum(trade_amount),2)   as salesAmount, "
                + "       sum(trade_quantity)          as salesQuantity, "
                + "       count(*)                     as tradeCnt "
                + "  from hui_min_dwd.dwd_trade_detail "
                + " where dt = ? "
                + " group by pay_type "
                + " order by tradeCnt desc";
        return jdbcTemplate.query(sql, new Object[]{dt},
                new BeanPropertyRowMapper<>(CategoryShareVO.class));
    }

    /**
     * 查询可用的业务日期列表（用于前端日期下拉框）。
     */
    public List<String> queryAvailableDates() {
        String sql = "select distinct dt from dws_store_sales_daily order by dt desc limit 60";
        return jdbcTemplate.queryForList(sql, String.class);
    }
}
