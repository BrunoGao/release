/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
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

package com.ljwx.modules.health.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.bo.TDeviceMessageDepartmentBO;
import com.ljwx.modules.health.domain.dto.device.message.department.TDeviceMessageDepartmentAddDTO;
import com.ljwx.modules.health.domain.dto.device.message.department.TDeviceMessageDepartmentDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.message.department.TDeviceMessageDepartmentSearchDTO;
import com.ljwx.modules.health.domain.dto.device.message.department.TDeviceMessageDepartmentUpdateDTO;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDepartment;
import com.ljwx.modules.health.domain.vo.TDeviceMessageDepartmentVO;
import com.ljwx.modules.health.facade.ITDeviceMessageDepartmentFacade;
import com.ljwx.modules.health.service.ITDeviceMessageDepartmentService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.device.facade.impl.TDeviceMessageDepartmentFacadeImpl
 * @CreateTime 2025-03-03 - 20:20:27
 */

@Service
@RequiredArgsConstructor
public class TDeviceMessageDepartmentFacadeImpl implements ITDeviceMessageDepartmentFacade {

    @NonNull
    private ITDeviceMessageDepartmentService tDeviceMessageDepartmentService;

    @Override
    public RPage<TDeviceMessageDepartmentVO> listTDeviceMessageDepartmentPage(PageQuery pageQuery, TDeviceMessageDepartmentSearchDTO tDeviceMessageDepartmentSearchDTO) {
        TDeviceMessageDepartmentBO tDeviceMessageDepartmentBO = CglibUtil.convertObj(tDeviceMessageDepartmentSearchDTO, TDeviceMessageDepartmentBO::new);
        IPage<TDeviceMessageDepartment> tDeviceMessageDepartmentIPage = tDeviceMessageDepartmentService.listTDeviceMessageDepartmentPage(pageQuery, tDeviceMessageDepartmentBO);
        return RPage.build(tDeviceMessageDepartmentIPage, TDeviceMessageDepartmentVO::new);
    }

    @Override
    public TDeviceMessageDepartmentVO get(Long id) {
        TDeviceMessageDepartment byId = tDeviceMessageDepartmentService.getById(id);
        return CglibUtil.convertObj(byId, TDeviceMessageDepartmentVO::new);
    }

    @Override
    @Transactional
    public boolean add(TDeviceMessageDepartmentAddDTO tDeviceMessageDepartmentAddDTO) {
        TDeviceMessageDepartmentBO tDeviceMessageDepartmentBO = CglibUtil.convertObj(tDeviceMessageDepartmentAddDTO, TDeviceMessageDepartmentBO::new);
        return tDeviceMessageDepartmentService.save(tDeviceMessageDepartmentBO);
    }

    @Override
    @Transactional
    public boolean update(TDeviceMessageDepartmentUpdateDTO tDeviceMessageDepartmentUpdateDTO) {
        TDeviceMessageDepartmentBO tDeviceMessageDepartmentBO = CglibUtil.convertObj(tDeviceMessageDepartmentUpdateDTO, TDeviceMessageDepartmentBO::new);
        return tDeviceMessageDepartmentService.updateById(tDeviceMessageDepartmentBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TDeviceMessageDepartmentDeleteDTO tDeviceMessageDepartmentDeleteDTO) {
        TDeviceMessageDepartmentBO tDeviceMessageDepartmentBO = CglibUtil.convertObj(tDeviceMessageDepartmentDeleteDTO, TDeviceMessageDepartmentBO::new);
        return tDeviceMessageDepartmentService.removeBatchByIds(tDeviceMessageDepartmentBO.getIds(), true);
    }

}