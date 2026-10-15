package com.huimin.retail.service;

import com.huimin.retail.dao.StoreSalesDAO;
import com.huimin.retail.vo.CategoryShareVO;
import com.huimin.retail.vo.StoreSalesVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * 业务层：承载业务规则（默认日期、参数规范化、取值范围约束）。
 * Controller 只负责参数接收与响应封装，业务规则集中在此处，
 * 便于被多个接口复用与单独测试。
 */
@Service
public class StoreSalesService {

    @Autowired
    private StoreSalesDAO storeSalesDAO;

    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyyMMdd");

    /** 业务规则：日期为空时取当天；TOP N 默认 10，限制在 1~50 */
    public List<StoreSalesVO> getStoreSalesTopN(String dt, String region, Integer topN) {
        return storeSalesDAO.queryStoreSalesTopN(normalizeDt(dt), region, normalizeTopN(topN));
    }

    public List<StoreSalesVO> getRegionSummary(String dt) {
        return storeSalesDAO.queryRegionSummary(normalizeDt(dt));
    }

    public List<CategoryShareVO> getCategoryShare(String dt) {
        return storeSalesDAO.queryCategoryShare(normalizeDt(dt));
    }

    public List<CategoryShareVO> getGoodsTopN(String dt, Integer topN) {
        return storeSalesDAO.queryGoodsTopN(normalizeDt(dt), normalizeTopN(topN));
    }

    public List<CategoryShareVO> getPayTypeDist(String dt) {
        return storeSalesDAO.queryPayTypeDist(normalizeDt(dt));
    }

    public List<String> getAvailableDates() {
        return storeSalesDAO.queryAvailableDates();
    }

    /** 默认取当天 —— 生产环境为 T+1 报表，实际可改为取昨天 */
    private String normalizeDt(String dt) {
        if (dt == null || dt.trim().isEmpty()) {
            return LocalDate.now().format(FMT);
        }
        return dt.trim();
    }

    private int normalizeTopN(Integer topN) {
        if (topN == null || topN <= 0) {
            return 10;
        }
        return Math.min(topN, 50);
    }
}
