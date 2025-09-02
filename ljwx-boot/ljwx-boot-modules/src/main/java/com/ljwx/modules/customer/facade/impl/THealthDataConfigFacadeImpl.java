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

package com.ljwx.modules.customer.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.bo.THealthDataConfigBO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigUpdateDTO;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.domain.vo.THealthDataConfigVO;
import com.ljwx.modules.customer.facade.ITHealthDataConfigFacade;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.customer.facade.impl.THealthDataConfigFacadeImpl
 * @CreateTime 2024-12-29 - 15:02:31
 */

@Service
@RequiredArgsConstructor
public class THealthDataConfigFacadeImpl implements ITHealthDataConfigFacade {

    @NonNull
    private ITHealthDataConfigService tHealthDataConfigService;

    @Override
    public RPage<THealthDataConfigVO> listTHealthDataConfigPage(PageQuery pageQuery, THealthDataConfigSearchDTO tHealthDataConfigSearchDTO) {
        THealthDataConfigBO tHealthDataConfigBO = CglibUtil.convertObj(tHealthDataConfigSearchDTO, THealthDataConfigBO::new);
        IPage<THealthDataConfig> tHealthDataConfigIPage = tHealthDataConfigService.listTHealthDataConfigPage(pageQuery, tHealthDataConfigBO);
        return RPage.build(tHealthDataConfigIPage, THealthDataConfigVO::new);
    }

    @Override
    public THealthDataConfigVO get(Long id) {
        THealthDataConfig byId = tHealthDataConfigService.getById(id);
        return CglibUtil.convertObj(byId, THealthDataConfigVO::new);
    }

    @Override
    @Transactional
    public boolean add(THealthDataConfigAddDTO tHealthDataConfigAddDTO) {
        THealthDataConfigBO tHealthDataConfigBO = CglibUtil.convertObj(tHealthDataConfigAddDTO, THealthDataConfigBO::new);
        return tHealthDataConfigService.save(tHealthDataConfigBO);
    }

    @Override
    @Transactional
    public boolean update(THealthDataConfigUpdateDTO tHealthDataConfigUpdateDTO) {
        THealthDataConfigBO tHealthDataConfigBO = CglibUtil.convertObj(tHealthDataConfigUpdateDTO, THealthDataConfigBO::new);
        System.out.println("Updating BO: " + tHealthDataConfigBO);
        boolean result = tHealthDataConfigService.updateById(tHealthDataConfigBO);
        System.out.println("Update Result: " + result);
        return result;
    }

    @Override
    @Transactional
    public boolean batchDelete(THealthDataConfigDeleteDTO tHealthDataConfigDeleteDTO) {
        THealthDataConfigBO tHealthDataConfigBO = CglibUtil.convertObj(tHealthDataConfigDeleteDTO, THealthDataConfigBO::new);
        return tHealthDataConfigService.removeBatchByIds(tHealthDataConfigBO.getIds(), true);
    }

}