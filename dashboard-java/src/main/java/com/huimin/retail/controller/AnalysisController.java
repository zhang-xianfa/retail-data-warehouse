package com.huimin.retail.controller;

import com.huimin.retail.common.Result;
import com.huimin.retail.service.StoreSalesService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 零售经营分析接口。
 * 统一前缀 /api/retail，返回值统一为 {code, msg, data}。
 */
@RestController
@RequestMapping("/api/retail")
public class AnalysisController {

    @Autowired
    private StoreSalesService storeSalesService;

    /**
     * 门店销售额 TOP N。
     * 示例：/api/retail/store/salesTop10?dt=20240520&region=华北&topN=10
     */
    @GetMapping("/store/salesTop10")
    public Result<?> storeSalesTop10(
            @RequestParam(value = "dt", required = false) String dt,
            @RequestParam(value = "region", required = false) String region,
            @RequestParam(value = "topN", required = false) Integer topN) {
        return Result.success(storeSalesService.getStoreSalesTopN(dt, region, topN));
    }

    /**
     * 各大区销售汇总。
     * 示例：/api/retail/region/sales?dt=20240520
     */
    @GetMapping("/region/sales")
    public Result<?> regionSales(
            @RequestParam(value = "dt", required = false) String dt) {
        return Result.success(storeSalesService.getRegionSummary(dt));
    }

    /**
     * 商品品类销售占比。
     * 示例：/api/retail/category/share?dt=20240520
     */
    @GetMapping("/category/share")
    public Result<?> categoryShare(
            @RequestParam(value = "dt", required = false) String dt) {
        return Result.success(storeSalesService.getCategoryShare(dt));
    }

    /**
     * 商品销售额 TOP N（热销商品分析）。
     * 示例：/api/retail/goods/top10?dt=20240520&topN=10
     */
    @GetMapping("/goods/top10")
    public Result<?> goodsTop10(
            @RequestParam(value = "dt", required = false) String dt,
            @RequestParam(value = "topN", required = false) Integer topN) {
        return Result.success(storeSalesService.getGoodsTopN(dt, topN));
    }

    /**
     * 支付方式分布。
     * 示例：/api/retail/pay/dist?dt=20240520
     */
    @GetMapping("/pay/dist")
    public Result<?> payDist(
            @RequestParam(value = "dt", required = false) String dt) {
        return Result.success(storeSalesService.getPayTypeDist(dt));
    }

    /**
     * 可用业务日期列表。
     * 示例：/api/retail/dates
     */
    @GetMapping("/dates")
    public Result<?> dates() {
        return Result.success(storeSalesService.getAvailableDates());
    }

    /**
     * 健康检查：确认后端与 Hive 数仓连通。
     * 示例：/api/retail/health
     */
    @GetMapping("/health")
    public Result<?> health() {
        try {
            int n = storeSalesService.getAvailableDates().size();
            return Result.success("Hive 连接正常，可用日期数 = " + n);
        } catch (Exception e) {
            return Result.fail("Hive 连接失败：" + e.getMessage());
        }
    }
}
