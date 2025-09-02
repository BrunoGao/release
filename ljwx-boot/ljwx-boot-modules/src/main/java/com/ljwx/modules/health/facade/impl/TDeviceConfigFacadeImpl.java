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
import com.ljwx.modules.health.domain.bo.TDeviceConfigBO;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigAddDTO;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigSearchDTO;
import com.ljwx.modules.health.domain.dto.device.config.TDeviceConfigUpdateDTO;
import com.ljwx.modules.health.domain.entity.TDeviceConfig;
import com.ljwx.modules.health.domain.vo.TDeviceConfigVO;
import com.ljwx.modules.health.facade.ITDeviceConfigFacade;
import com.ljwx.modules.health.service.ITDeviceConfigService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import lombok.NonNull;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TDeviceConfigFacadeImpl
 * @CreateTime 2024-10-21 - 19:44:31
 */

@Service
@RequiredArgsConstructor
public class TDeviceConfigFacadeImpl implements ITDeviceConfigFacade {

    @NonNull
    private ITDeviceConfigService tDeviceConfigService;

    @Override
    public RPage<TDeviceConfigVO> listTDeviceConfigPage(PageQuery pageQuery, TDeviceConfigSearchDTO tDeviceConfigSearchDTO) {
        TDeviceConfigBO tDeviceConfigBO = CglibUtil.convertObj(tDeviceConfigSearchDTO, TDeviceConfigBO::new);
        IPage<TDeviceConfig> tDeviceConfigIPage = tDeviceConfigService.listTDeviceConfigPage(pageQuery, tDeviceConfigBO);
        return RPage.build(tDeviceConfigIPage, TDeviceConfigVO::new);
    }

    @Override
    public TDeviceConfigVO get(Long id) {
        TDeviceConfig byId = tDeviceConfigService.getById(id);
        return CglibUtil.convertObj(byId, TDeviceConfigVO::new);
    }

    @Override
    @Transactional
    public boolean add(TDeviceConfigAddDTO tDeviceConfigAddDTO) {
        TDeviceConfigBO tDeviceConfigBO = CglibUtil.convertObj(tDeviceConfigAddDTO, TDeviceConfigBO::new);
        return tDeviceConfigService.save(tDeviceConfigBO);
    }

    @Override
    @Transactional
    public boolean update(TDeviceConfigUpdateDTO tDeviceConfigUpdateDTO) {
        TDeviceConfigBO tDeviceConfigBO = CglibUtil.convertObj(tDeviceConfigUpdateDTO, TDeviceConfigBO::new);
        return tDeviceConfigService.updateById(tDeviceConfigBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TDeviceConfigDeleteDTO tDeviceConfigDeleteDTO) {
        TDeviceConfigBO tDeviceConfigBO = CglibUtil.convertObj(tDeviceConfigDeleteDTO, TDeviceConfigBO::new);
        return tDeviceConfigService.removeBatchByIds(tDeviceConfigBO.getIds(), true);
    }

}