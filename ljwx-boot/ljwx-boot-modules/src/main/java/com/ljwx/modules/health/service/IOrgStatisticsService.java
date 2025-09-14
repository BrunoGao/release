package com.ljwx.modules.health.service;

import com.ljwx.modules.health.domain.vo.OrgStatisticsVO;

/**
 * @author brunoGao
 * @version $ v 0.1 2025/3/7 23:16 Exp $$
 */

public interface IOrgStatisticsService {
    OrgStatisticsVO getOrgStatistics(String orgId);
    
    /**
     * 根据orgId获取组织统计信息
     * 支持多级部门管理员登录
     * @param orgId 组织ID
     * @return 组织统计信息
     */
    OrgStatisticsVO getOrgStatisticsByOrgId(String orgId);
}
