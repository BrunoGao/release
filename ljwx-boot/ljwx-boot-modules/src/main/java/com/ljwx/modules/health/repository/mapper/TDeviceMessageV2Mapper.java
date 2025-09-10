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

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ljwx.modules.health.domain.entity.TDeviceMessageV2;
import com.ljwx.modules.health.domain.dto.v2.message.MessageQueryV2DTO;
import com.ljwx.modules.health.domain.vo.v2.TDeviceMessageV2VO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * V2设备消息Mapper接口
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.repository.mapper.TDeviceMessageV2Mapper
 * @CreateTime 2025-09-10 - 16:15:00
 */
@Mapper
public interface TDeviceMessageV2Mapper extends BaseMapper<TDeviceMessageV2> {

    /**
     * 分页查询V2消息
     */
    Page<TDeviceMessageV2VO> selectMessagePage(Page<TDeviceMessageV2VO> page, @Param("query") MessageQueryV2DTO query);

    /**
     * 根据设备序列号查询消息
     */
    List<TDeviceMessageV2> selectByDeviceSn(@Param("deviceSn") String deviceSn, @Param("limit") Integer limit);

    /**
     * 根据组织ID查询消息
     */
    List<TDeviceMessageV2> selectByOrgId(@Param("orgId") Long orgId, @Param("limit") Integer limit);

    /**
     * 根据租户ID查询消息
     */
    List<TDeviceMessageV2> selectByCustomerId(@Param("customerId") Long customerId, @Param("limit") Integer limit);

    /**
     * 查询即将过期的消息
     */
    List<TDeviceMessageV2> selectExpiringSoon(@Param("hours") Integer hours);

    /**
     * 查询高优先级未处理消息
     */
    List<TDeviceMessageV2> selectHighPriorityPending(@Param("customerId") Long customerId);

    /**
     * 查询紧急未处理消息
     */
    List<TDeviceMessageV2> selectUrgentPending(@Param("customerId") Long customerId);

    /**
     * 批量更新消息状态
     */
    int batchUpdateStatus(@Param("ids") List<Long> ids, @Param("status") String status);

    /**
     * 统计消息数量按状态
     */
    List<Map<String, Object>> countByStatus(@Param("customerId") Long customerId, @Param("orgId") Long orgId);

    /**
     * 统计消息数量按类型
     */
    List<Map<String, Object>> countByType(@Param("customerId") Long customerId, @Param("orgId") Long orgId);

    /**
     * 统计消息数量按紧急程度
     */
    List<Map<String, Object>> countByUrgency(@Param("customerId") Long customerId, @Param("orgId") Long orgId);

    /**
     * 统计消息数量按设备
     */
    List<Map<String, Object>> countByDevice(@Param("customerId") Long customerId, @Param("orgId") Long orgId, @Param("limit") Integer limit);

    /**
     * 统计消息数量按日期
     */
    List<Map<String, Object>> countByDate(@Param("customerId") Long customerId, @Param("orgId") Long orgId, @Param("days") Integer days);

    /**
     * 统计消息数量按小时
     */
    List<Map<String, Object>> countByHour(@Param("customerId") Long customerId, @Param("orgId") Long orgId, @Param("date") LocalDateTime date);

    /**
     * 获取活跃设备数量
     */
    Long countActiveDevices(@Param("customerId") Long customerId, @Param("orgId") Long orgId, @Param("hours") Integer hours);

    /**
     * 获取活跃组织数量
     */
    Long countActiveOrgs(@Param("customerId") Long customerId, @Param("hours") Integer hours);

    /**
     * 获取平均响应时间
     */
    Double getAverageResponseTime(@Param("customerId") Long customerId, @Param("orgId") Long orgId, @Param("hours") Integer hours);

    /**
     * 获取发送成功率
     */
    Double getSendSuccessRate(@Param("customerId") Long customerId, @Param("orgId") Long orgId, @Param("hours") Integer hours);

    /**
     * 删除过期消息
     */
    int deleteExpiredMessages(@Param("beforeTime") LocalDateTime beforeTime);

    /**
     * 清理旧数据
     */
    int cleanupOldData(@Param("beforeTime") LocalDateTime beforeTime, @Param("batchSize") Integer batchSize);
}