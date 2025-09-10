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

package com.ljwx.modules.customer.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.customer.domain.bo.THealthDataConfigBO;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.repository.mapper.THealthDataConfigMapper;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.customer.service.HealthDataConfigCacheService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.Arrays;
import java.util.List;
/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.customer.service.impl.THealthDataConfigServiceImpl
 * @CreateTime 2024-12-29 - 15:02:31
 */

@Slf4j
@Service
@RequiredArgsConstructor 
public class THealthDataConfigServiceImpl extends ServiceImpl<THealthDataConfigMapper, THealthDataConfig> implements ITHealthDataConfigService {

    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @NonNull
    private HealthDataConfigCacheService healthDataConfigCacheService;

    @Override
    public IPage<THealthDataConfig> listTHealthDataConfigPage(PageQuery pageQuery, THealthDataConfigBO tHealthDataConfigBO) {

        Long customerId = tHealthDataConfigBO.getCustomerId();
        System.out.println("customerId: " + customerId);
        Long firstParent = sysOrgUnitsService.getFirstParent(customerId);
        System.out.println("firstParent: " + firstParent);

        LambdaQueryWrapper<THealthDataConfig> queryWrapper = new LambdaQueryWrapper<THealthDataConfig>()
            .eq(ObjectUtils.isNotEmpty(firstParent), THealthDataConfig::getCustomerId, firstParent)
            .eq(ObjectUtils.isNotEmpty(tHealthDataConfigBO.getDataType()), THealthDataConfig::getDataType, tHealthDataConfigBO.getDataType())
            .orderByDesc(THealthDataConfig::getCreateTime);
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

    @Override
    public List<THealthDataConfig> getEnabledConfigsByCustomerId(Long customerId) {
        return list(new LambdaQueryWrapper<THealthDataConfig>()
            .eq(THealthDataConfig::getIsEnabled, 1)
            .eq(THealthDataConfig::getCustomerId, customerId)
            .orderByDesc(THealthDataConfig::getWeight));
    }

    @Override
    public List<THealthDataConfig> getBaseConfigsByCustomerId(Long customerId) {
        // 定义t_user_health_data主表的基础体征字段（排除复杂的分表数据）
        List<String> baseMetrics = Arrays.asList(
            "heart_rate",      // 心率
            "blood_oxygen",    // 血氧
            "temperature",     // 体温  
            "pressure_high",   // 收缩压
            "pressure_low",    // 舒张压
            "step",            // 步数
            "stress",          // 压力
            "calorie",         // 卡路里
            "distance"         // 距离
        );
        
        return list(new LambdaQueryWrapper<THealthDataConfig>()
            .eq(THealthDataConfig::getIsEnabled, 1)
            .eq(THealthDataConfig::getCustomerId, customerId)
            .in(THealthDataConfig::getDataType, baseMetrics)
            .orderByDesc(THealthDataConfig::getWeight));
    }

    @Override
    public List<THealthDataConfig> getEnabledConfigsByOrgId(Long orgId) {
        // 获取顶级部门ID用于查询配置
        Long topLevelDeptId = sysOrgUnitsService.getTopLevelDeptIdByOrgId(orgId);
        
        return list(new LambdaQueryWrapper<THealthDataConfig>()
            .eq(THealthDataConfig::getIsEnabled, 1)
            .eq(THealthDataConfig::getCustomerId, topLevelDeptId)
            .orderByDesc(THealthDataConfig::getWeight));
    }

    @Override
    public List<THealthDataConfig> getBaseConfigsByOrgId(Long orgId) {
        // 定义需要过滤掉的字段
        List<String> excludedTypes = Arrays.asList(
            "location", "wear", "ecg", "exercise_daily", 
            "exercise_week", "scientific_sleep", "work_out"
        );
        
        // 获取顶级部门ID用于查询配置
        Long topLevelDeptId = sysOrgUnitsService.getTopLevelDeptIdByOrgId(orgId);
        
        return list(new LambdaQueryWrapper<THealthDataConfig>()
            .eq(THealthDataConfig::getIsEnabled, 1)
            .eq(THealthDataConfig::getCustomerId, topLevelDeptId)
            .notIn(THealthDataConfig::getDataType, excludedTypes)
            .orderByDesc(THealthDataConfig::getWeight));
    }

    /**
     * 覆盖保存方法，添加缓存失效
     */
    @Override
    public boolean save(THealthDataConfig entity) {
        boolean result = super.save(entity);
        if (result && entity.getCustomerId() != null) {
            // 失效缓存并发布事件
            healthDataConfigCacheService.invalidateCache(entity.getCustomerId());
            log.info("🔄 健康配置保存后缓存失效: customer_id={}", entity.getCustomerId());
        }
        return result;
    }

    /**
     * 覆盖更新方法，添加缓存失效
     */
    @Override
    public boolean updateById(THealthDataConfig entity) {
        boolean result = super.updateById(entity);
        if (result && entity.getCustomerId() != null) {
            // 失效缓存并发布事件
            healthDataConfigCacheService.invalidateCache(entity.getCustomerId());
            log.info("🔄 健康配置更新后缓存失效: customer_id={}", entity.getCustomerId());
        }
        return result;
    }

    /**
     * 覆盖批量删除方法，添加缓存失效
     */
    @Override
    public boolean removeBatchByIds(java.util.Collection<?> list) {
        // 删除前先获取所有相关的customer_id
        List<THealthDataConfig> configsToDelete = listByIds((java.util.Collection<? extends java.io.Serializable>) list);
        List<Long> customerIds = configsToDelete.stream()
            .map(THealthDataConfig::getCustomerId)
            .distinct()
            .filter(id -> id != null)
            .collect(java.util.stream.Collectors.toList());
        
        boolean result = super.removeBatchByIds(list);
        
        if (result && !customerIds.isEmpty()) {
            // 失效所有相关租户的缓存
            customerIds.forEach(customerId -> {
                healthDataConfigCacheService.invalidateCache(customerId);
                log.info("🔄 健康配置删除后缓存失效: customer_id={}", customerId);
            });
        }
        
        return result;
    }

}

