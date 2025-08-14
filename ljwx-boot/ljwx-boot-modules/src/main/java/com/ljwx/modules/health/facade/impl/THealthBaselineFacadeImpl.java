/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (paynezhuang@gmail.com)]
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
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.bo.THealthBaselineBO;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineAddDTO;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineDeleteDTO;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineSearchDTO;
import com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineUpdateDTO;
import com.ljwx.modules.health.domain.entity.THealthBaseline;
import com.ljwx.modules.health.domain.vo.THealthBaselineVO;
import com.ljwx.modules.health.facade.ITHealthBaselineFacade;
import com.ljwx.modules.health.service.ITHealthBaselineService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.ljwx.common.util.CglibUtil;

/**
 * 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.THealthBaselineFacadeImpl
 * @CreateTime 2025-05-04 - 14:13:02
 */

@Service
@RequiredArgsConstructor
public class THealthBaselineFacadeImpl implements ITHealthBaselineFacade {

    @NonNull
    private ITHealthBaselineService tHealthBaselineService;

    @Override
    public RPage<THealthBaselineVO> listTHealthBaselinePage(PageQuery pageQuery, THealthBaselineSearchDTO tHealthBaselineSearchDTO) {
        THealthBaselineBO tHealthBaselineBO = CglibUtil.convertObj(tHealthBaselineSearchDTO, THealthBaselineBO::new);
        IPage<THealthBaseline> tHealthBaselineIPage = tHealthBaselineService.listTHealthBaselinePage(pageQuery, tHealthBaselineBO);
        return RPage.build(tHealthBaselineIPage, THealthBaselineVO::new);
    }

    @Override
    public THealthBaselineVO get(Long id) {
        THealthBaseline byId = tHealthBaselineService.getById(id);
        return CglibUtil.convertObj(byId, THealthBaselineVO::new);
    }

    @Override
    @Transactional
    public boolean add(THealthBaselineAddDTO tHealthBaselineAddDTO) {
        THealthBaselineBO tHealthBaselineBO = CglibUtil.convertObj(tHealthBaselineAddDTO, THealthBaselineBO::new);
        return tHealthBaselineService.save(tHealthBaselineBO);
    }

    @Override
    @Transactional
    public boolean update(THealthBaselineUpdateDTO tHealthBaselineUpdateDTO) {
        THealthBaselineBO tHealthBaselineBO = CglibUtil.convertObj(tHealthBaselineUpdateDTO, THealthBaselineBO::new);
        return tHealthBaselineService.updateById(tHealthBaselineBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(THealthBaselineDeleteDTO tHealthBaselineDeleteDTO) {
        THealthBaselineBO tHealthBaselineBO = CglibUtil.convertObj(tHealthBaselineDeleteDTO, THealthBaselineBO::new);
        return tHealthBaselineService.removeBatchByIds(tHealthBaselineBO.getIds(), true);
    }

}