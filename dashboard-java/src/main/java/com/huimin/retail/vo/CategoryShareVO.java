package com.huimin.retail.vo;

import lombok.Data;

/**
 * 商品品类销量占比视图对象（用于饼图）。
 */
@Data
public class CategoryShareVO {

    /** 品类名称：生鲜 / 日用品 / 家电 */
    private String categoryName;
    /** 销售额（元） */
    private Double salesAmount;
    /** 销量（件） */
    private Integer salesQuantity;
    /** 交易笔数 */
    private Integer tradeCnt;
}
