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

import java.time.LocalDateTime;
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
        // 使用自定义查询，直接包含用户名关联
        IPage<TAlertInfo> page = pageQuery.buildPage();
        return baseMapper.listAlertInfoWithUserName(page, tTAlertInfoBO);
    }
    
    @Override
    public IPage<TAlertInfo> listAlertInfoByOrgOptimized(PageQuery pageQuery, Long orgId, 
            Long customerId, String alertType, String alertStatus) {
        IPage<TAlertInfo> page = pageQuery.buildPage();
        return baseMapper.listAlertInfoByOrgOptimized(page, orgId, customerId, alertType, alertStatus);
    }
    
    @Override
    public List<Map<String, Object>> getAlertStatsByUser(Long orgId, Long customerId, 
            LocalDateTime startTime, LocalDateTime endTime) {
        return baseMapper.getAlertStatsByUser(orgId, customerId, startTime, endTime);
    }
}

