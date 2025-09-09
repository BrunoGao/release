/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.health.service;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.bo.TAlertInfoBO;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.baomidou.mybatisplus.extension.service.IService;
import com.baomidou.mybatisplus.core.metadata.IPage;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 *  Service 服务接口层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.ITAlertInfoService
 * @CreateTime 2024-10-27 - 20:37:23
 */

public interface ITAlertInfoService extends IService<TAlertInfo> {

    /**
     *  - 分页查询
     *
     * @param pageQuery 分页对象
     * @param tTAlertInfoBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author payne.zhuang
     * @CreateTime 2024-10-27 - 20:37:23
     */
    IPage<TAlertInfo> listTAlertInfoPage(PageQuery pageQuery, TAlertInfoBO tTAlertInfoBO);
    
    /**
     * 高性能组织级告警查询 - 利用sys_user的org_id优化
     *
     * @param pageQuery 分页对象
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param alertType 告警类型
     * @param alertStatus 告警状态
     * @return {@link IPage} 分页结果
     * @author bruno.gao
     * @CreateTime 2025-01-26
     */
    IPage<TAlertInfo> listAlertInfoByOrgOptimized(PageQuery pageQuery, Long orgId, 
            Long customerId, String alertType, String alertStatus);
    
    /**
     * 用户告警统计查询 - 利用sys_user优化避免多表JOIN
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @return {@link List} 统计结果
     * @author bruno.gao
     * @CreateTime 2025-01-26
     */
    List<Map<String, Object>> getAlertStatsByUser(Long orgId, Long customerId, 
            LocalDateTime startTime, LocalDateTime endTime);
}
