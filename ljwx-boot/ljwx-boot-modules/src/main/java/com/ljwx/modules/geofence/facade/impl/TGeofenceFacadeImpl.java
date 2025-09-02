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

package com.ljwx.modules.geofence.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.geofence.domain.bo.TGeofenceBO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceAddDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceDeleteDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceSearchDTO;
import com.ljwx.modules.geofence.domain.dto.geofence.TGeofenceUpdateDTO;
import com.ljwx.modules.geofence.domain.entity.TGeofence;
import com.ljwx.modules.geofence.domain.vo.TGeofenceVO;
import com.ljwx.modules.geofence.facade.ITGeofenceFacade;
import com.ljwx.modules.geofence.service.ITGeofenceService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.geofence.facade.impl.TGeofenceFacadeImpl
 * @CreateTime 2025-01-07 - 19:44:06
 */

@Service
@RequiredArgsConstructor
public class TGeofenceFacadeImpl implements ITGeofenceFacade {

    @NonNull
    private ITGeofenceService tGeofenceService;

    @Override
    public RPage<TGeofenceVO> listTGeofencePage(PageQuery pageQuery, TGeofenceSearchDTO tGeofenceSearchDTO) {
        TGeofenceBO tGeofenceBO = CglibUtil.convertObj(tGeofenceSearchDTO, TGeofenceBO::new);
        IPage<TGeofence> tGeofenceIPage = tGeofenceService.listTGeofencePage(pageQuery, tGeofenceBO);
        return RPage.build(tGeofenceIPage, TGeofenceVO::new);
    }

    @Override
    public TGeofenceVO get(Long id) {
        TGeofence byId = tGeofenceService.getById(id);
        return CglibUtil.convertObj(byId, TGeofenceVO::new);
    }

    @Override
    @Transactional
    public boolean add(TGeofenceAddDTO tGeofenceAddDTO) {
        TGeofenceBO tGeofenceBO = CglibUtil.convertObj(tGeofenceAddDTO, TGeofenceBO::new);
        return tGeofenceService.save(tGeofenceBO);
    }

    @Override
    @Transactional
    public boolean update(TGeofenceUpdateDTO tGeofenceUpdateDTO) {
        TGeofenceBO tGeofenceBO = CglibUtil.convertObj(tGeofenceUpdateDTO, TGeofenceBO::new);
        return tGeofenceService.updateById(tGeofenceBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TGeofenceDeleteDTO tGeofenceDeleteDTO) {
        TGeofenceBO tGeofenceBO = CglibUtil.convertObj(tGeofenceDeleteDTO, TGeofenceBO::new);
        return tGeofenceService.removeBatchByIds(tGeofenceBO.getIds(), true);
    }

}