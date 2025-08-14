package com.ljwx.admin.controller.health;

import com.ljwx.common.api.Result;
import com.ljwx.modules.health.domain.vo.OrgStatisticsVO;
import com.ljwx.modules.health.service.IOrgStatisticsService;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/health")

public class OrgStatisticsController {

    @Autowired
    private IOrgStatisticsService orgStatisticsService;

    @GetMapping("/gather_total_info")

    public Result<OrgStatisticsVO> getOrgStatistics(
        @RequestParam("customer_id") String customerId
    ) {
        log.info("Getting organization statistics for customer_id: {}", customerId);
        OrgStatisticsVO statistics = orgStatisticsService.getOrgStatistics(customerId);
        return Result.data(statistics);
    }
}