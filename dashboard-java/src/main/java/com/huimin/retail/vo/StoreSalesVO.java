package com.huimin.retail.vo;

import lombok.Data;

/**
 * 门店销售汇总视图对象。
 * 字段与前端图表所需数据一一对应，SQL 查询时通过「列别名 = 属性名」完成映射，
 * 避免把数据库列名直接暴露给前端。
 */
@Data
public class StoreSalesVO {

    /** 门店ID */
    private String storeId;
    /** 门店名称 */
    private String storeName;
    /** 所属大区 */
    private String storeRegion;
    /** 销售额（元） */
    private Double salesAmount;
    /** 销量（件） */
    private Integer salesQuantity;
    /** 订单数（去重交易时间点数） */
    private Integer orderCnt;
    /** 客单价（元） */
    private Double avgOrderAmount;
}
