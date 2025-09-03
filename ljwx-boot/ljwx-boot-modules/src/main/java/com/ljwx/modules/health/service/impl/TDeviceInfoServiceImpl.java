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
        // 🔧 设备过滤逻辑: 根据用户ID或部门ID过滤设备，特殊处理orgId=0的情况
        System.out.println("🔍 查询条件 - userIdStr: " + tDeviceInfoBO.getUserIdStr() + ", orgId: " + tDeviceInfoBO.getOrgId());
        System.out.println("🔍 过滤条件判断 - userIdStr isEmpty: " + ObjectUtils.isEmpty(tDeviceInfoBO.getUserIdStr()) 
            + ", orgId isEmpty: " + ObjectUtils.isEmpty(tDeviceInfoBO.getOrgId()) 
            + ", orgId equals 0: " + (tDeviceInfoBO.getOrgId() != null && tDeviceInfoBO.getOrgId().equals(0L)));
        
        // 当有具体的用户ID或者部门ID不为空且不为0时进行过滤
        if (ObjectUtils.isNotEmpty(tDeviceInfoBO.getUserIdStr()) || 
           (ObjectUtils.isNotEmpty(tDeviceInfoBO.getOrgId()) && !tDeviceInfoBO.getOrgId().equals(0L))) {
            
            System.out.println("🔍 开始调用 getDeviceSnList 进行设备过滤...");
            List<String> deviceSnList = deviceUserMappingService.getDeviceSnList(
                tDeviceInfoBO.getUserIdStr(),
                tDeviceInfoBO.getOrgId() != null ? String.valueOf(tDeviceInfoBO.getOrgId()) : null
            );

            System.out.println("✅ 获取设备列表: " + (deviceSnList != null ? deviceSnList.toString() : "null"));
            
            if (deviceSnList == null || deviceSnList.isEmpty()) {
                System.out.println("⚠️ 设备列表为空，返回空页面");
                return pageQuery.buildPage();
            }
            
            List<String> validDeviceSnList = deviceSnList.stream()
                .filter(Objects::nonNull)
                .filter(sn -> !sn.trim().isEmpty())
                .distinct()
                .collect(Collectors.toList());
            
            System.out.println("✅ 过滤后有效设备列表: " + validDeviceSnList.toString());
            
            if (validDeviceSnList.isEmpty()) {
                System.out.println("⚠️ 有效设备列表为空，返回空页面");
                return pageQuery.buildPage();
            }
            
            queryWrapper.in(TDeviceInfo::getSerialNumber, validDeviceSnList);
            System.out.println("✅ 已添加设备序列号过滤条件");
        } else {
            System.out.println("⚠️ 跳过设备过滤，将查询所有设备");
        }

        // 执行分页查询
        IPage<TDeviceInfo> page = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);

        // 获取所有不重复的deviceSn
        Set<String> deviceSns = page.getRecords().stream()
            .map(TDeviceInfo::getSerialNumber)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        // 获取设备关联的用户和部门信息
        Map<String, IDeviceUserMappingService.UserInfo> deviceUserMap = deviceUserMappingService.getDeviceUserInfo(deviceSns);

        // 为每条记录添加用户和部门信息
        page.getRecords().forEach(record -> {
            if (record.getSerialNumber() != null) {
                IDeviceUserMappingService.UserInfo userInfo = deviceUserMap.get(record.getSerialNumber());
                if (userInfo != null) {
                    record.setUserName(userInfo.getUserName());
                    // Note: departmentInfo field removed as entity only has orgId
                }
            }
        });

        return page;
    }

}

