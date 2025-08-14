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
import com.ljwx.modules.health.domain.bo.TDeviceMessageBO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageAddDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageSearchDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageUpdateDTO;
import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.vo.TDeviceMessageVO;
import com.ljwx.modules.health.facade.ITDeviceMessageFacade;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import lombok.NonNull;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TDeviceMessageFacadeImpl
 * @CreateTime 2024-10-24 - 13:07:24
 */

@Service
@RequiredArgsConstructor
public class TDeviceMessageFacadeImpl implements ITDeviceMessageFacade {

    @NonNull
    private ITDeviceMessageService tDeviceMessageService;

    @Override
    public RPage<TDeviceMessageVO> listTDeviceMessagePage(PageQuery pageQuery, TDeviceMessageSearchDTO tDeviceMessageSearchDTO) {
        TDeviceMessageBO tDeviceMessageBO = CglibUtil.convertObj(tDeviceMessageSearchDTO, TDeviceMessageBO::new);
        IPage<TDeviceMessageVO> tDeviceMessageIPage = tDeviceMessageService.listTDeviceMessagePage(pageQuery, tDeviceMessageBO);
        return RPage.build(tDeviceMessageIPage, TDeviceMessageVO::new);
    }

    @Override
    public TDeviceMessageVO get(Long id) {
        TDeviceMessage byId = tDeviceMessageService.getById(id);
        return CglibUtil.convertObj(byId, TDeviceMessageVO::new);
    }

    @Override
    @Transactional
    public boolean add(TDeviceMessageAddDTO tDeviceMessageAddDTO) {
        TDeviceMessageBO tDeviceMessageBO = CglibUtil.convertObj(tDeviceMessageAddDTO, TDeviceMessageBO::new);
        System.out.println("tDeviceMessageBO: " + tDeviceMessageBO.toString());
        return tDeviceMessageService.save(tDeviceMessageBO);
    }

    @Override
    @Transactional
    public boolean update(TDeviceMessageUpdateDTO tDeviceMessageUpdateDTO) {
        TDeviceMessageBO tDeviceMessageBO = CglibUtil.convertObj(tDeviceMessageUpdateDTO, TDeviceMessageBO::new);
        return tDeviceMessageService.updateById(tDeviceMessageBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TDeviceMessageDeleteDTO tDeviceMessageDeleteDTO) {
        TDeviceMessageBO tDeviceMessageBO = CglibUtil.convertObj(tDeviceMessageDeleteDTO, TDeviceMessageBO::new);
        return tDeviceMessageService.removeBatchByIds(tDeviceMessageBO.getIds(), true);
    }

}