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
import com.ljwx.modules.health.domain.entity.THealthDataSlowWeekly;
import com.ljwx.modules.health.repository.mapper.THealthDataSlowWeeklyMapper;
import com.ljwx.modules.health.service.ITHealthDataSlowWeeklyService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.TemporalAdjusters;
import java.util.List;

/**
 * 用户健康数据周报 Service 实现类
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName THealthDataSlowWeeklyServiceImpl
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
public class THealthDataSlowWeeklyServiceImpl extends ServiceImpl<THealthDataSlowWeeklyMapper, THealthDataSlowWeekly> 
    implements ITHealthDataSlowWeeklyService {

    @Override
    public THealthDataSlowWeekly getByDeviceSnAndWeekStart(String deviceSn, LocalDate weekStart) {
        return this.getOne(new LambdaQueryWrapper<THealthDataSlowWeekly>()
                .eq(THealthDataSlowWeekly::getDeviceSn, deviceSn)
                .eq(THealthDataSlowWeekly::getTimestamp, weekStart));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveOrUpdate(THealthDataSlowWeekly weeklyData) {
        try {
            // 查找是否存在
            THealthDataSlowWeekly existing = getByDeviceSnAndWeekStart(weeklyData.getDeviceSn(), weeklyData.getTimestamp());
            
            LocalDateTime now = LocalDateTime.now();
            
            if (existing != null) {
                // 更新现有记录
                weeklyData.setId(existing.getId());
                weeklyData.setCreateTime(existing.getCreateTime());
                weeklyData.setUpdateTime(now);
                return this.updateById(weeklyData);
            } else {
                // 插入新记录
                weeklyData.setCreateTime(now);
                weeklyData.setUpdateTime(now);
                return this.save(weeklyData);
            }
        } catch (Exception e) {
            log.error("保存或更新每周健康数据失败: deviceSn={}, weekStart={}", 
                weeklyData.getDeviceSn(), weeklyData.getTimestamp(), e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchSaveOrUpdate(List<THealthDataSlowWeekly> weeklyDataList) {
        try {
            for (THealthDataSlowWeekly weeklyData : weeklyDataList) {
                if (!saveOrUpdate(weeklyData)) {
                    return false;
                }
            }
            return true;
        } catch (Exception e) {
            log.error("批量保存或更新每周健康数据失败", e);
            return false;
        }
    }

    @Override
    public List<THealthDataSlowWeekly> listByUserIdAndDateRange(Long userId, LocalDate startDate, LocalDate endDate) {
        return this.list(new LambdaQueryWrapper<THealthDataSlowWeekly>()
                .eq(THealthDataSlowWeekly::getUserId, userId)
                .ge(THealthDataSlowWeekly::getTimestamp, startDate)
                .le(THealthDataSlowWeekly::getTimestamp, endDate)
                .orderByDesc(THealthDataSlowWeekly::getTimestamp));
    }

    @Override
    public List<THealthDataSlowWeekly> listByOrgIdAndDateRange(Long orgId, LocalDate startDate, LocalDate endDate) {
        return this.list(new LambdaQueryWrapper<THealthDataSlowWeekly>()
                .eq(THealthDataSlowWeekly::getOrgId, orgId)
                .ge(THealthDataSlowWeekly::getTimestamp, startDate)
                .le(THealthDataSlowWeekly::getTimestamp, endDate)
                .orderByDesc(THealthDataSlowWeekly::getTimestamp));
    }

    @Override
    public LocalDate getWeekStart(LocalDate date) {
        // 获取指定日期所在周的周一
        return date.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
    }
}