package com.ljwx.modules.health.service;

import com.ljwx.modules.health.domain.vo.OrgStatisticsVO;

/**
 * @author brunoGao
 * @version $ v 0.1 2025/3/7 23:16 Exp $$
 */

public interface IOrgStatisticsService {
    OrgStatisticsVO getOrgStatistics(String orgId);
}
