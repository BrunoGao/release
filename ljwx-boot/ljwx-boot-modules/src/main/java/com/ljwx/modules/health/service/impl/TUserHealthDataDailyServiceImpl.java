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
import com.ljwx.modules.health.domain.entity.TUserHealthDataDaily;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataDailyMapper;
import com.ljwx.modules.health.service.ITUserHealthDataDailyService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 用户健康数据日报 Service 实现类
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName TUserHealthDataDailyServiceImpl
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
public class TUserHealthDataDailyServiceImpl extends ServiceImpl<TUserHealthDataDailyMapper, TUserHealthDataDaily> 
    implements ITUserHealthDataDailyService {

    @Override
    public TUserHealthDataDaily getByDeviceSnAndDate(String deviceSn, LocalDate date) {
        return this.getOne(new LambdaQueryWrapper<TUserHealthDataDaily>()
                .eq(TUserHealthDataDaily::getDeviceSn, deviceSn)
                .eq(TUserHealthDataDaily::getTimestamp, date));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveOrUpdate(TUserHealthDataDaily dailyData) {
        try {
            // 查找是否存在
            TUserHealthDataDaily existing = getByDeviceSnAndDate(dailyData.getDeviceSn(), dailyData.getTimestamp());
            
            LocalDateTime now = LocalDateTime.now();
            
            if (existing != null) {
                // 更新现有记录
                dailyData.setId(existing.getId());
                dailyData.setCreateTime(existing.getCreateTime());
                dailyData.setUpdateTime(now);
                return this.updateById(dailyData);
            } else {
                // 插入新记录
                dailyData.setCreateTime(now);
                dailyData.setUpdateTime(now);
                return this.save(dailyData);
            }
        } catch (Exception e) {
            log.error("保存或更新每日健康数据失败: deviceSn={}, date={}", 
                dailyData.getDeviceSn(), dailyData.getTimestamp(), e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchSaveOrUpdate(List<TUserHealthDataDaily> dailyDataList) {
        try {
            for (TUserHealthDataDaily dailyData : dailyDataList) {
                if (!saveOrUpdate(dailyData)) {
                    return false;
                }
            }
            return true;
        } catch (Exception e) {
            log.error("批量保存或更新每日健康数据失败", e);
            return false;
        }
    }

    @Override
    public List<TUserHealthDataDaily> listByUserIdAndDateRange(Long userId, LocalDate startDate, LocalDate endDate) {
        return this.list(new LambdaQueryWrapper<TUserHealthDataDaily>()
                .eq(TUserHealthDataDaily::getUserId, userId)
                .ge(TUserHealthDataDaily::getTimestamp, startDate)
                .le(TUserHealthDataDaily::getTimestamp, endDate)
                .orderByDesc(TUserHealthDataDaily::getTimestamp));
    }

    @Override
    public List<TUserHealthDataDaily> listByOrgIdAndDateRange(Long orgId, LocalDate startDate, LocalDate endDate) {
        return this.list(new LambdaQueryWrapper<TUserHealthDataDaily>()
                .eq(TUserHealthDataDaily::getOrgId, orgId)
                .ge(TUserHealthDataDaily::getTimestamp, startDate)
                .le(TUserHealthDataDaily::getTimestamp, endDate)
                .orderByDesc(TUserHealthDataDaily::getTimestamp));
    }
}