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
import com.ljwx.modules.health.domain.bo.TWechatAlertConfigBO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigAddDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.config.wechat.TWechatAlertConfigUpdateDTO;
import com.ljwx.modules.health.domain.entity.TWechatAlertConfig;
import com.ljwx.modules.health.domain.vo.TWechatAlertConfigVO;
import com.ljwx.modules.health.facade.ITWechatAlertConfigFacade;
import com.ljwx.modules.health.service.ITWechatAlertConfigService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Table to store WeChat alert configuration 门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TWechatAlertConfigFacadeImpl
 * @CreateTime 2025-01-02 - 13:17:05
 */

@Service
@RequiredArgsConstructor
public class TWechatAlertConfigFacadeImpl implements ITWechatAlertConfigFacade {

    @NonNull
    private ITWechatAlertConfigService tWechatAlertConfigService;

    @Override
    public RPage<TWechatAlertConfigVO> listTWechatAlertConfigPage(PageQuery pageQuery, TWechatAlertConfigSearchDTO tWechatAlertConfigSearchDTO) {
        TWechatAlertConfigBO tWechatAlertConfigBO = CglibUtil.convertObj(tWechatAlertConfigSearchDTO, TWechatAlertConfigBO::new);
        IPage<TWechatAlertConfig> tWechatAlertConfigIPage = tWechatAlertConfigService.listTWechatAlertConfigPage(pageQuery, tWechatAlertConfigBO);
        return RPage.build(tWechatAlertConfigIPage, TWechatAlertConfigVO::new);
    }

    @Override
    public TWechatAlertConfigVO get(Long id) {
        TWechatAlertConfig byId = tWechatAlertConfigService.getById(id);
        return CglibUtil.convertObj(byId, TWechatAlertConfigVO::new);
    }

    @Override
    @Transactional
    public boolean add(TWechatAlertConfigAddDTO tWechatAlertConfigAddDTO) {
        TWechatAlertConfigBO tWechatAlertConfigBO = CglibUtil.convertObj(tWechatAlertConfigAddDTO, TWechatAlertConfigBO::new);
        return tWechatAlertConfigService.save(tWechatAlertConfigBO);
    }

    @Override
    @Transactional
    public boolean update(TWechatAlertConfigUpdateDTO tWechatAlertConfigUpdateDTO) {
        TWechatAlertConfigBO tWechatAlertConfigBO = CglibUtil.convertObj(tWechatAlertConfigUpdateDTO, TWechatAlertConfigBO::new);
        return tWechatAlertConfigService.updateById(tWechatAlertConfigBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TWechatAlertConfigDeleteDTO tWechatAlertConfigDeleteDTO) {
        TWechatAlertConfigBO tWechatAlertConfigBO = CglibUtil.convertObj(tWechatAlertConfigDeleteDTO, TWechatAlertConfigBO::new);
        return tWechatAlertConfigService.removeBatchByIds(tWechatAlertConfigBO.getIds(), true);
    }

}