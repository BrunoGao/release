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
import com.ljwx.modules.health.domain.bo.TDeviceMessageDetailBO;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailAddDTO;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailSearchDTO;
import com.ljwx.modules.health.domain.dto.device.message.detail.TDeviceMessageDetailUpdateDTO;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetail;
import com.ljwx.modules.health.domain.vo.TDeviceMessageDetailVO;
import com.ljwx.modules.health.facade.ITDeviceMessageDetailFacade;
import com.ljwx.modules.health.service.ITDeviceMessageDetailService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TDeviceMessageDetailFacadeImpl
 * @CreateTime 2025-03-05 - 19:57:37
 */

@Service
@RequiredArgsConstructor
public class TDeviceMessageDetailFacadeImpl implements ITDeviceMessageDetailFacade {

    @NonNull
    private ITDeviceMessageDetailService tDeviceMessageDetailService;

    @Override
    public RPage<TDeviceMessageDetailVO> listTDeviceMessageDetailPage(PageQuery pageQuery, TDeviceMessageDetailSearchDTO tDeviceMessageDetailSearchDTO) {
        TDeviceMessageDetailBO tDeviceMessageDetailBO = CglibUtil.convertObj(tDeviceMessageDetailSearchDTO, TDeviceMessageDetailBO::new);
        IPage<TDeviceMessageDetail> tDeviceMessageDetailIPage = tDeviceMessageDetailService.listTDeviceMessageDetailPage(pageQuery, tDeviceMessageDetailBO);
        return RPage.build(tDeviceMessageDetailIPage, TDeviceMessageDetailVO::new);
    }

    @Override
    public TDeviceMessageDetailVO get(Long id) {
        TDeviceMessageDetail byId = tDeviceMessageDetailService.getById(id);
        return CglibUtil.convertObj(byId, TDeviceMessageDetailVO::new);
    }

    @Override
    @Transactional
    public boolean add(TDeviceMessageDetailAddDTO tDeviceMessageDetailAddDTO) {
        TDeviceMessageDetailBO tDeviceMessageDetailBO = CglibUtil.convertObj(tDeviceMessageDetailAddDTO, TDeviceMessageDetailBO::new);
        return tDeviceMessageDetailService.save(tDeviceMessageDetailBO);
    }

    @Override
    @Transactional
    public boolean update(TDeviceMessageDetailUpdateDTO tDeviceMessageDetailUpdateDTO) {
        TDeviceMessageDetailBO tDeviceMessageDetailBO = CglibUtil.convertObj(tDeviceMessageDetailUpdateDTO, TDeviceMessageDetailBO::new);
        return tDeviceMessageDetailService.updateById(tDeviceMessageDetailBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TDeviceMessageDetailDeleteDTO tDeviceMessageDetailDeleteDTO) {
        TDeviceMessageDetailBO tDeviceMessageDetailBO = CglibUtil.convertObj(tDeviceMessageDetailDeleteDTO, TDeviceMessageDetailBO::new);
        return tDeviceMessageDetailService.removeBatchByIds(tDeviceMessageDetailBO.getIds(), true);
    }

}