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

package com.ljwx.modules.health.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.bo.TDeviceUserBO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserAddDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserSearchDTO;
import com.ljwx.modules.health.domain.dto.device.user.TDeviceUserUpdateDTO;
import com.ljwx.modules.health.domain.entity.TDeviceUser;
import com.ljwx.modules.health.domain.vo.TDeviceUserVO;
import com.ljwx.modules.health.facade.ITDeviceUserFacade;
import com.ljwx.modules.health.service.ITDeviceUserService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 设备与用户关联表 门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TDeviceUserFacadeImpl
 * @CreateTime 2025-01-03 - 15:12:29
 */

@Service
@RequiredArgsConstructor
public class TDeviceUserFacadeImpl implements ITDeviceUserFacade {

    @NonNull
    private ITDeviceUserService tDeviceUserService;

    @Override
    public RPage<TDeviceUserVO> listTDeviceUserPage(PageQuery pageQuery, TDeviceUserSearchDTO tDeviceUserSearchDTO) {
        TDeviceUserBO tDeviceUserBO = CglibUtil.convertObj(tDeviceUserSearchDTO, TDeviceUserBO::new);
        IPage<TDeviceUserVO> tDeviceUserIPage = tDeviceUserService.listTDeviceUserPage(pageQuery, tDeviceUserBO);
        return RPage.build(tDeviceUserIPage, TDeviceUserVO::new);
    }

    @Override
    public TDeviceUserVO get(Long id) {
        TDeviceUser byId = tDeviceUserService.getById(id);
        return CglibUtil.convertObj(byId, TDeviceUserVO::new);
    }

    @Override
    @Transactional
    public boolean add(TDeviceUserAddDTO tDeviceUserAddDTO) {
        TDeviceUserBO tDeviceUserBO = CglibUtil.convertObj(tDeviceUserAddDTO, TDeviceUserBO::new);
        return tDeviceUserService.save(tDeviceUserBO);
    }

    @Override
    @Transactional
    public boolean update(TDeviceUserUpdateDTO tDeviceUserUpdateDTO) {
        TDeviceUserBO tDeviceUserBO = CglibUtil.convertObj(tDeviceUserUpdateDTO, TDeviceUserBO::new);
        return tDeviceUserService.updateById(tDeviceUserBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TDeviceUserDeleteDTO tDeviceUserDeleteDTO) {
        TDeviceUserBO tDeviceUserBO = CglibUtil.convertObj(tDeviceUserDeleteDTO, TDeviceUserBO::new);
        return tDeviceUserService.removeBatchByIds(tDeviceUserBO.getIds(), true);
    }

}