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
import com.ljwx.modules.health.domain.bo.TAlertActionLogBO;
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogAddDTO;
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.action.log.TAlertActionLogUpdateDTO;
import com.ljwx.modules.health.domain.entity.TAlertActionLog;
import com.ljwx.modules.health.domain.vo.TAlertActionLogVO;
import com.ljwx.modules.health.facade.ITAlertActionLogFacade;
import com.ljwx.modules.health.service.ITAlertActionLogService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TAlertActionLogFacadeImpl
 * @CreateTime 2024-10-27 - 21:37:48
 */

@Service
@RequiredArgsConstructor
public class TAlertActionLogFacadeImpl implements ITAlertActionLogFacade {

    @NonNull
    private ITAlertActionLogService tAlertActionLogService;

    @Override
    public RPage<TAlertActionLogVO> listTAlertActionLogPage(PageQuery pageQuery, TAlertActionLogSearchDTO tAlertActionLogSearchDTO) {
        TAlertActionLogBO tAlertActionLogBO = CglibUtil.convertObj(tAlertActionLogSearchDTO, TAlertActionLogBO::new);
        IPage<TAlertActionLog> tAlertActionLogIPage = tAlertActionLogService.listTAlertActionLogPage(pageQuery, tAlertActionLogBO);
        return RPage.build(tAlertActionLogIPage, TAlertActionLogVO::new);
    }

    @Override
    public TAlertActionLogVO get(Long id) {
        TAlertActionLog byId = tAlertActionLogService.getById(id);
        return CglibUtil.convertObj(byId, TAlertActionLogVO::new);
    }

    @Override
    @Transactional
    public boolean add(TAlertActionLogAddDTO tAlertActionLogAddDTO) {
        TAlertActionLogBO tAlertActionLogBO = CglibUtil.convertObj(tAlertActionLogAddDTO, TAlertActionLogBO::new);
        return tAlertActionLogService.save(tAlertActionLogBO);
    }

    @Override
    @Transactional
    public boolean update(TAlertActionLogUpdateDTO tAlertActionLogUpdateDTO) {
        TAlertActionLogBO tAlertActionLogBO = CglibUtil.convertObj(tAlertActionLogUpdateDTO, TAlertActionLogBO::new);
        return tAlertActionLogService.updateById(tAlertActionLogBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TAlertActionLogDeleteDTO tAlertActionLogDeleteDTO) {
        TAlertActionLogBO tAlertActionLogBO = CglibUtil.convertObj(tAlertActionLogDeleteDTO, TAlertActionLogBO::new);
        return tAlertActionLogService.removeBatchByIds(tAlertActionLogBO.getIds(), true);
    }

}