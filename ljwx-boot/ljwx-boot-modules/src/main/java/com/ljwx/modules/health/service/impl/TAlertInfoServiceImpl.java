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
    public IPage<TAlertInfo> listTAlertInfoPage(PageQuery pageQuery, TAlertInfoBO tAlertInfoBO) {
        
        LambdaQueryWrapper<TAlertInfo> queryWrapper = new LambdaQueryWrapper<TAlertInfo>()
            .eq(ObjectUtils.isNotEmpty(tAlertInfoBO.getAlertType()), TAlertInfo::getAlertType, tAlertInfoBO.getAlertType())
            .eq(ObjectUtils.isNotEmpty(tAlertInfoBO.getAlertStatus()), TAlertInfo::getAlertStatus, tAlertInfoBO.getAlertStatus())
            .orderByDesc(TAlertInfo::getAlertTimestamp);

        // 添加租户过滤 - 直接使用传入的customerId
        if (tAlertInfoBO.getCustomerId() != null && tAlertInfoBO.getCustomerId() != 0L) {
            // 租户用户，查看全局告警(customer_id=0)和自己租户的告警
            queryWrapper.and(wrapper -> 
                wrapper.eq(TAlertInfo::getCustomerId, 0L)
                       .or()
                       .eq(TAlertInfo::getCustomerId, tAlertInfoBO.getCustomerId())
            );
        }
        if (ObjectUtils.isNotEmpty(tAlertInfoBO.getUserId()) || ObjectUtils.isNotEmpty(tAlertInfoBO.getDepartmentInfo())) {
            // 获取设备序列号列表
            List<String> deviceSnList = deviceUserMappingService.getDeviceSnList(
                tAlertInfoBO.getUserId() != null ? tAlertInfoBO.getUserId().toString() : null,
                tAlertInfoBO.getDepartmentInfo()
            );
            
            // 如果设备列表为空，直接返回空结果
            if (deviceSnList.isEmpty()) {
                return pageQuery.buildPage();
            }
            
                // 添加设备序列号条件
                queryWrapper.in(TAlertInfo::getDeviceSn, deviceSnList);
        }

        IPage<TAlertInfo> page = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);

        // 获取所有不重复的deviceSn
        Set<String> deviceSns = page.getRecords().stream()
            .map(TAlertInfo::getDeviceSn)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        // 获取设备关联的用户和部门信息
        Map<String, IDeviceUserMappingService.UserInfo> deviceUserMap = deviceUserMappingService.getDeviceUserInfo(deviceSns);

        // 为每条记录添加用户和部门信息
        page.getRecords().forEach(record -> {
            if (record.getDeviceSn() != null) {
                IDeviceUserMappingService.UserInfo userInfo = deviceUserMap.get(record.getDeviceSn());
                if (userInfo != null) {
                    record.setUserName(userInfo.getUserName());
                    record.setDepartmentInfo(userInfo.getDepartmentName());
                }
            }
        });

        return page;
    }
}

