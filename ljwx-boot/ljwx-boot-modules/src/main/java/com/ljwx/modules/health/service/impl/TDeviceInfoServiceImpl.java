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
import com.ljwx.modules.health.domain.bo.TDeviceInfoBO;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.repository.mapper.TDeviceInfoMapper;
import com.ljwx.modules.health.service.IDeviceUserMappingService;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceInfoServiceImpl
 * @CreateTime 2024-12-14 - 21:31:16
 */

@Service
public class TDeviceInfoServiceImpl extends ServiceImpl<TDeviceInfoMapper, TDeviceInfo> implements ITDeviceInfoService {

    @Autowired
    private IDeviceUserMappingService deviceUserMappingService;


    @Override
    public IPage<TDeviceInfo> listTDeviceInfoPage(PageQuery pageQuery, TDeviceInfoBO tDeviceInfoBO) {
        // 构建基本查询条件
        LambdaQueryWrapper<TDeviceInfo> queryWrapper = new LambdaQueryWrapper<TDeviceInfo>()
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getChargingStatus()), TDeviceInfo::getChargingStatus, tDeviceInfoBO.getChargingStatus())
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getWearableStatus()), TDeviceInfo::getWearableStatus, tDeviceInfoBO.getWearableStatus())
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getModel()), TDeviceInfo::getModel, tDeviceInfoBO.getModel())
        .eq(ObjectUtils.isNotEmpty(tDeviceInfoBO.getStatus()), TDeviceInfo::getStatus, tDeviceInfoBO.getStatus())
        .inSql(TDeviceInfo::getId, "SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY serial_number ORDER BY timestamp DESC) as rn FROM t_device_info) t WHERE rn = 1")
        .orderByDesc(TDeviceInfo::getTimestamp);

        // 添加租户过滤 - 直接使用传入的customerId
        if (tDeviceInfoBO.getCustomerId() != null && tDeviceInfoBO.getCustomerId() != 0L) {
            // 租户用户，查看全局设备(customer_id=0)和自己租户的设备
            queryWrapper.and(wrapper -> 
                wrapper.eq(TDeviceInfo::getCustomerId, 0L)
                       .or()
                       .eq(TDeviceInfo::getCustomerId, tDeviceInfoBO.getCustomerId())
            );
        }
        // 🔧 设备过滤逻辑: 直接使用userId和orgId过滤，不再通过deviceSn转换
        System.out.println("🔍 查询条件 - userIdStr: " + tDeviceInfoBO.getUserIdStr() + ", orgId: " + tDeviceInfoBO.getOrgId() + ", customerId: " + tDeviceInfoBO.getCustomerId());
        
        // 直接使用userId过滤（如果指定）
        if (ObjectUtils.isNotEmpty(tDeviceInfoBO.getUserIdStr()) && 
            !"0".equals(tDeviceInfoBO.getUserIdStr()) && 
            !"all".equals(tDeviceInfoBO.getUserIdStr())) {
            try {
                Long userId = Long.parseLong(tDeviceInfoBO.getUserIdStr());
                queryWrapper.eq(TDeviceInfo::getUserId, userId);
                System.out.println("✅ 添加userId过滤条件: " + userId);
            } catch (NumberFormatException e) {
                System.err.println("❌ userId格式错误: " + tDeviceInfoBO.getUserIdStr());
            }
        }
        
        // 直接使用orgId过滤（如果指定）
        if (ObjectUtils.isNotEmpty(tDeviceInfoBO.getOrgId()) && 
            !tDeviceInfoBO.getOrgId().equals(0L)) {
            queryWrapper.eq(TDeviceInfo::getOrgId, tDeviceInfoBO.getOrgId());
            System.out.println("✅ 添加orgId过滤条件: " + tDeviceInfoBO.getOrgId());
        }

        // 执行分页查询
        IPage<TDeviceInfo> page = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);

        // 获取所有不重复的userId和orgId，批量获取用户和部门信息
        Set<Long> userIds = page.getRecords().stream()
            .map(TDeviceInfo::getUserId)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());
        
        Set<Long> orgIds = page.getRecords().stream()
            .map(TDeviceInfo::getOrgId)
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

