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

package com.ljwx.modules.customer.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.bo.TCustomerConfigBO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigUpdateDTO;
import com.ljwx.modules.customer.domain.entity.TCustomerConfig;
import com.ljwx.modules.customer.domain.vo.TCustomerConfigVO;
import com.ljwx.modules.customer.facade.ITCustomerConfigFacade;
import com.ljwx.modules.customer.service.ITCustomerConfigService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.customer.facade.impl.TCustomerConfigFacadeImpl
 * @CreateTime 2024-12-29 - 15:33:30
 */

@Service
@RequiredArgsConstructor
public class TCustomerConfigFacadeImpl implements ITCustomerConfigFacade {

    @NonNull
    private ITCustomerConfigService tCustomerConfigService;

    @Override
    public RPage<TCustomerConfigVO> listTCustomerConfigPage(PageQuery pageQuery, TCustomerConfigSearchDTO tCustomerConfigSearchDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigSearchDTO, TCustomerConfigBO::new);
        IPage<TCustomerConfig> tCustomerConfigIPage = tCustomerConfigService.listTCustomerConfigPage(pageQuery, tCustomerConfigBO);
        return RPage.build(tCustomerConfigIPage, TCustomerConfigVO::new);
    }

    @Override
    public TCustomerConfigVO get(Long id) {
        TCustomerConfig byId = tCustomerConfigService.getById(id);
        return CglibUtil.convertObj(byId, TCustomerConfigVO::new);
    }

    @Override
    @Transactional
    public boolean add(TCustomerConfigAddDTO tCustomerConfigAddDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigAddDTO, TCustomerConfigBO::new);
        return tCustomerConfigService.save(tCustomerConfigBO);
    }

    @Override
    @Transactional
    public boolean update(TCustomerConfigUpdateDTO tCustomerConfigUpdateDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigUpdateDTO, TCustomerConfigBO::new);
        return tCustomerConfigService.updateById(tCustomerConfigBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigDeleteDTO, TCustomerConfigBO::new);
        return tCustomerConfigService.removeBatchByIds(tCustomerConfigBO.getIds(), true);
    }

}