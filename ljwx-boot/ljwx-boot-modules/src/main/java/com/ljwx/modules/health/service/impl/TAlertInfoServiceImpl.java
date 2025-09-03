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
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.bo.TAlertInfoBO;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.repository.mapper.TAlertInfoMapper;
import com.ljwx.modules.health.service.IDeviceUserMappingService;
import com.ljwx.modules.health.service.ITAlertInfoService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TAlertInfoServiceImpl
 * @CreateTime 2024-12-15 - 22:04:51
 */

@Service
public class TAlertInfoServiceImpl extends ServiceImpl<TAlertInfoMapper, TAlertInfo> implements ITAlertInfoService {

    @Autowired
    private IDeviceUserMappingService deviceUserMappingService;


    @Override
    public IPage<TAlertInfo> listTAlertInfoPage(PageQuery pageQuery, TAlertInfoBO tTAlertInfoBO) {
        
        LambdaQueryWrapper<TAlertInfo> queryWrapper = new LambdaQueryWrapper<TAlertInfo>()
            .eq(ObjectUtils.isNotEmpty(tTAlertInfoBO.getAlertType()), TAlertInfo::getAlertType, tTAlertInfoBO.getAlertType())
            .eq(ObjectUtils.isNotEmpty(tTAlertInfoBO.getAlertStatus()), TAlertInfo::getAlertStatus, tTAlertInfoBO.getAlertStatus())
            .orderByDesc(TAlertInfo::getAlertTimestamp);

        // 添加租户过滤 - 直接使用传入的customerId
        if (tTAlertInfoBO.getCustomerId() != null && tTAlertInfoBO.getCustomerId() != 0L) {
            // 租户用户，查看全局告警(customer_id=0)和自己租户的告警
            queryWrapper.and(wrapper -> 
                wrapper.eq(TAlertInfo::getCustomerId, 0L)
                       .or()
                       .eq(TAlertInfo::getCustomerId, tTAlertInfoBO.getCustomerId())
            );
        }
        
        // 直接使用userId和orgId过滤，不再通过deviceSn转换
        System.out.println("🔍 告警查询 - userId: " + tTAlertInfoBO.getUserId() + ", orgId: " + tTAlertInfoBO.getOrgId() + ", customerId: " + tTAlertInfoBO.getCustomerId());
        
        // 直接使用userId过滤（如果指定）
        if (ObjectUtils.isNotEmpty(tTAlertInfoBO.getUserId())) {
            queryWrapper.eq(TAlertInfo::getUserId, tTAlertInfoBO.getUserId());
            System.out.println("✅ 添加userId过滤条件: " + tTAlertInfoBO.getUserId());
        }
        
        // 直接使用orgId过滤（如果指定）
        if (ObjectUtils.isNotEmpty(tTAlertInfoBO.getOrgId())) {
            queryWrapper.eq(TAlertInfo::getOrgId, tTAlertInfoBO.getOrgId());
            System.out.println("✅ 添加orgId过滤条件: " + tTAlertInfoBO.getOrgId());
        }

        IPage<TAlertInfo> page = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);

        // 获取所有不重复的userId和orgId，批量获取用户和部门信息
        Set<Long> userIds = page.getRecords().stream()
            .map(TAlertInfo::getUserId)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());
        
        Set<Long> orgIds = page.getRecords().stream()
            .map(TAlertInfo::getOrgId)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        // 批量获取用户信息
        Map<Long, String> userIdToNameMap = new HashMap<>();
        if (!userIds.isEmpty()) {
            // 这里需要添加用户服务的批量查询方法
            // userIdToNameMap = sysUserService.getUserNamesMapByIds(userIds);
        }
        
        // 批量获取部门信息  
        Map<Long, String> orgIdToNameMap = new HashMap<>();
        if (!orgIds.isEmpty()) {
            // 这里需要添加部门服务的批量查询方法
            // orgIdToNameMap = sysOrgUnitsService.getOrgNamesMapByIds(orgIds);
        }

        // 为每条记录添加用户和部门信息
        page.getRecords().forEach(record -> {
            if (record.getUserId() != null) {
                String userName = userIdToNameMap.get(record.getUserId());
                if (userName != null) {
                    record.setUserName(userName);
                }
            }
            // 注意：这里不再设置departmentInfo字段，因为实体中只有orgId
        });

        return page;
    }
}

