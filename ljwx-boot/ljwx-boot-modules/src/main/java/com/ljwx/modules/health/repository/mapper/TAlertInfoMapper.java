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

package com.ljwx.modules.health.repository.mapper;

import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;

/**
 *  Mapper 接口层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.repository.mapper.TAlertInfoMapper
 * @CreateTime 2024-10-27 - 23:00:41
 */

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.modules.health.domain.bo.TAlertInfoBO;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public interface TAlertInfoMapper extends BaseMapper<TAlertInfo> {

    IPage<TAlertInfo> listAlertInfoWithUserName(IPage<TAlertInfo> page, @Param("bo") TAlertInfoBO tAlertInfoBO);
    
    /**
     * 高性能组织级告警查询 - 利用sys_user的org_id优化
     */
    IPage<TAlertInfo> listAlertInfoByOrgOptimized(IPage<TAlertInfo> page, 
            @Param("orgId") Long orgId,
            @Param("customerId") Long customerId,
            @Param("alertType") String alertType,
            @Param("alertStatus") String alertStatus);
    
    /**
     * 用户告警统计查询 - 利用sys_user优化避免多表JOIN
     */
    List<Map<String, Object>> getAlertStatsByUser(@Param("orgId") Long orgId,
            @Param("customerId") Long customerId,
            @Param("startTime") LocalDateTime startTime,
            @Param("endTime") LocalDateTime endTime);

}