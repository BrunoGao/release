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

package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.modules.health.domain.entity.TDeviceInfoHistory;
import com.ljwx.modules.health.repository.mapper.TDeviceInfoHistoryMapper;
import com.ljwx.modules.health.service.ITDeviceInfoHistoryService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 设备信息历史记录 Service 实现类
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName TDeviceInfoHistoryServiceImpl
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
public class TDeviceInfoHistoryServiceImpl extends ServiceImpl<TDeviceInfoHistoryMapper, TDeviceInfoHistory> 
    implements ITDeviceInfoHistoryService {

    @Override
    public List<TDeviceInfoHistory> listBySerialNumber(String serialNumber) {
        return this.list(new LambdaQueryWrapper<TDeviceInfoHistory>()
                .eq(TDeviceInfoHistory::getSerialNumber, serialNumber)
                .orderByDesc(TDeviceInfoHistory::getTimestamp));
    }

    @Override
    public List<TDeviceInfoHistory> listBySerialNumberAndTimeRange(String serialNumber, LocalDateTime startTime, LocalDateTime endTime) {
        return this.list(new LambdaQueryWrapper<TDeviceInfoHistory>()
                .eq(TDeviceInfoHistory::getSerialNumber, serialNumber)
                .ge(TDeviceInfoHistory::getTimestamp, startTime)
                .le(TDeviceInfoHistory::getTimestamp, endTime)
                .orderByDesc(TDeviceInfoHistory::getTimestamp));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveBatch(List<TDeviceInfoHistory> historyList) {
        try {
            return super.saveBatch(historyList);
        } catch (Exception e) {
            log.error("批量保存设备历史记录失败", e);
            return false;
        }
    }
}