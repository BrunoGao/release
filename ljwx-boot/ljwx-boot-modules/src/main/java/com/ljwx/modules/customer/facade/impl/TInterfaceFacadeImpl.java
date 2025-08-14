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
import com.ljwx.modules.customer.domain.bo.TInterfaceBO;
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceAddDTO;
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceDeleteDTO;
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceSearchDTO;
import com.ljwx.modules.customer.domain.dto.interfaces.TInterfaceUpdateDTO;
import com.ljwx.modules.customer.domain.entity.TInterface;
import com.ljwx.modules.customer.domain.vo.TInterfaceVO;
import com.ljwx.modules.customer.facade.ITInterfaceFacade;
import com.ljwx.modules.customer.service.ITInterfaceService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.customer.facade.impl.TInterfaceFacadeImpl
 * @CreateTime 2024-12-29 - 15:33:49
 */

@Service
@RequiredArgsConstructor
public class TInterfaceFacadeImpl implements ITInterfaceFacade {

    @NonNull
    private ITInterfaceService tInterfaceService;

    @Override
    public RPage<TInterfaceVO> listTInterfacePage(PageQuery pageQuery, TInterfaceSearchDTO tInterfaceSearchDTO) {
        TInterfaceBO tInterfaceBO = CglibUtil.convertObj(tInterfaceSearchDTO, TInterfaceBO::new);
        IPage<TInterface> tInterfaceIPage = tInterfaceService.listTInterfacePage(pageQuery, tInterfaceBO);
        return RPage.build(tInterfaceIPage, TInterfaceVO::new);
    }

    @Override
    public TInterfaceVO get(Long id) {
        TInterface byId = tInterfaceService.getById(id);
        return CglibUtil.convertObj(byId, TInterfaceVO::new);
    }

    @Override
    @Transactional
    public boolean add(TInterfaceAddDTO tInterfaceAddDTO) {
        TInterfaceBO tInterfaceBO = CglibUtil.convertObj(tInterfaceAddDTO, TInterfaceBO::new);
        return tInterfaceService.save(tInterfaceBO);
    }

    @Override
    @Transactional
    public boolean update(TInterfaceUpdateDTO tInterfaceUpdateDTO) {
        TInterfaceBO tInterfaceBO = CglibUtil.convertObj(tInterfaceUpdateDTO, TInterfaceBO::new);
        return tInterfaceService.updateById(tInterfaceBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TInterfaceDeleteDTO tInterfaceDeleteDTO) {
        TInterfaceBO tInterfaceBO = CglibUtil.convertObj(tInterfaceDeleteDTO, TInterfaceBO::new);
        return tInterfaceService.removeBatchByIds(tInterfaceBO.getIds(), true);
    }

}