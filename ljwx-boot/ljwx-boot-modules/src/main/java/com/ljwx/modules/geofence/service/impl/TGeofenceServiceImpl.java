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

package com.ljwx.modules.geofence.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.geofence.domain.bo.TGeofenceBO;
import com.ljwx.modules.geofence.domain.entity.TGeofence;
import com.ljwx.modules.geofence.repository.mapper.TGeofenceMapper;
import com.ljwx.modules.geofence.service.ITGeofenceService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.geofence.service.impl.TGeofenceServiceImpl
 * @CreateTime 2025-01-07 - 19:44:06
 */

@Service
public class TGeofenceServiceImpl extends ServiceImpl<TGeofenceMapper, TGeofence> implements ITGeofenceService {


    @Override
    public IPage<TGeofence> listTGeofencePage(PageQuery pageQuery, TGeofenceBO tGeofenceBO) {
        LambdaQueryWrapper<TGeofence> queryWrapper = new LambdaQueryWrapper<TGeofence>()
            .eq(ObjectUtils.isNotEmpty(tGeofenceBO.getName()), TGeofence::getName, tGeofenceBO.getName())
            .eq(ObjectUtils.isNotEmpty(tGeofenceBO.getStatus()), TGeofence::getStatus, tGeofenceBO.getStatus())
            .orderByDesc(TGeofence::getCreateTime);
        
        IPage<TGeofence> page = baseMapper.listGeofence(pageQuery.buildPage(), queryWrapper);
        
        // Log the area field for debugging
        page.getRecords().forEach(record -> {
            System.out.println("Area GeoJSON: " + record.getArea());
        });
        
        return page;
    }

}

