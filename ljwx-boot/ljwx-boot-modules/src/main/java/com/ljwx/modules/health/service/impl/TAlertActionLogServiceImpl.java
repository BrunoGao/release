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
import com.ljwx.modules.health.domain.bo.TAlertActionLogBO;
import com.ljwx.modules.health.domain.entity.TAlertActionLog;
import com.ljwx.modules.health.repository.mapper.TAlertActionLogMapper;
import com.ljwx.modules.health.service.ITAlertActionLogService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;
import com.ljwx.modules.health.service.IDeviceUserMappingService;

import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;
import java.util.Collections;
import java.util.ArrayList;
import java.util.stream.Collectors;

import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysUserOrg;
import com.ljwx.modules.system.service.ISysUserOrgService;

/**
 *  Service 服务接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TAlertActionLogServiceImpl
 * @CreateTime 2024-10-27 - 21:37:48
 */

@Service
public class TAlertActionLogServiceImpl extends ServiceImpl<TAlertActionLogMapper, TAlertActionLog> implements ITAlertActionLogService {

    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;

    @Autowired
    private ISysUserOrgService sysUserOrgService;

    @Override
    public IPage<TAlertActionLog> listTAlertActionLogPage(PageQuery pageQuery, TAlertActionLogBO tAlertActionLogBO) {
        LambdaQueryWrapper<TAlertActionLog> queryWrapper = new LambdaQueryWrapper<TAlertActionLog>()
            .eq(ObjectUtils.isNotEmpty(tAlertActionLogBO.getAlertId()), TAlertActionLog::getAlertId, tAlertActionLogBO.getAlertId())
            .eq(ObjectUtils.isNotEmpty(tAlertActionLogBO.getActionUser()), TAlertActionLog::getActionUser, tAlertActionLogBO.getActionUser())
            .eq(ObjectUtils.isNotEmpty(tAlertActionLogBO.getResult()), TAlertActionLog::getResult, tAlertActionLogBO.getResult())
            .orderByDesc(TAlertActionLog::getActionTimestamp);
        if (ObjectUtils.isNotEmpty(tAlertActionLogBO.getUserId()) && !"all".equals(tAlertActionLogBO.getUserId())) {
                queryWrapper.eq(TAlertActionLog::getActionUserId, tAlertActionLogBO.getUserId());
        }else if (ObjectUtils.isNotEmpty(tAlertActionLogBO.getDepartmentInfo())) {
                Long deptId = Long.parseLong(tAlertActionLogBO.getDepartmentInfo());
                List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(Collections.singletonList(deptId));
                
                List<String> allDeptIds = new ArrayList<>();
                allDeptIds.add(tAlertActionLogBO.getDepartmentInfo());
                if (descendants != null) {
                    allDeptIds.addAll(descendants.stream()
                        .map(unit -> String.valueOf(unit.getId()))
                        .collect(Collectors.toList()));
                }
                
                List<Long> userIds = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
                    .in(SysUserOrg::getOrgId, allDeptIds))
                    .stream()
                    .map(SysUserOrg::getUserId)
                    .collect(Collectors.toList());
                    
                if (!userIds.isEmpty()) {
                    queryWrapper.in(TAlertActionLog::getActionUserId, userIds);
                } 
        }
        queryWrapper.orderByDesc(TAlertActionLog::getActionTimestamp); 

        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

