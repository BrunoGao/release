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
import com.ljwx.modules.health.domain.entity.TDeviceInfoHistory;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 设备信息历史记录 Service 接口
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName ITDeviceInfoHistoryService
 * @CreateTime 2024-12-16
 */
public interface ITDeviceInfoHistoryService extends IService<TDeviceInfoHistory> {

    /**
     * 根据设备序列号查询历史记录
     *
     * @param serialNumber 设备序列号
     * @return 历史记录列表
     */
    List<TDeviceInfoHistory> listBySerialNumber(String serialNumber);

    /**
     * 根据设备序列号和时间范围查询历史记录
     *
     * @param serialNumber 设备序列号
     * @param startTime    开始时间
     * @param endTime      结束时间
     * @return 历史记录列表
     */
    List<TDeviceInfoHistory> listBySerialNumberAndTimeRange(String serialNumber, LocalDateTime startTime, LocalDateTime endTime);

    /**
     * 批量保存设备历史记录
     *
     * @param historyList 历史记录列表
     * @return 是否成功
     */
    boolean saveBatch(List<TDeviceInfoHistory> historyList);
}