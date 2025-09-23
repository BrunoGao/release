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

import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.modules.health.domain.entity.TUserHealthDataDaily;

import java.time.LocalDate;
import java.util.List;

/**
 * 用户健康数据日报 Service 服务接口层
 * 用于处理慢字段数据：sleep_data, exercise_daily_data, workout_data, scientific_sleep_data
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName ITUserHealthDataDailyService
 * @CreateTime 2024-12-16
 */
public interface ITUserHealthDataDailyService extends IService<TUserHealthDataDaily> {

    /**
     * 根据设备SN和日期查询每日数据
     * 
     * @param deviceSn 设备序列号
     * @param date 日期
     * @return 每日健康数据
     */
    TUserHealthDataDaily getByDeviceSnAndDate(String deviceSn, LocalDate date);

    /**
     * 保存或更新每日数据
     * 如果存在则更新，不存在则插入
     * 
     * @param dailyData 每日数据
     * @return 是否成功
     */
    boolean saveOrUpdate(TUserHealthDataDaily dailyData);

    /**
     * 批量保存或更新每日数据
     * 
     * @param dailyDataList 每日数据列表
     * @return 是否成功
     */
    boolean batchSaveOrUpdate(List<TUserHealthDataDaily> dailyDataList);

    /**
     * 根据用户ID和日期范围查询每日数据
     * 
     * @param userId 用户ID
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @return 每日数据列表
     */
    List<TUserHealthDataDaily> listByUserIdAndDateRange(Long userId, LocalDate startDate, LocalDate endDate);

    /**
     * 根据组织ID和日期范围查询每日数据
     * 
     * @param orgId 组织ID
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @return 每日数据列表
     */
    List<TUserHealthDataDaily> listByOrgIdAndDateRange(Long orgId, LocalDate startDate, LocalDate endDate);
}