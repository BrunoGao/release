/*
 * All Rights Reserved: Copyright [2024] [ljwx (paynezhuang@gmail.com)]
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
import com.ljwx.common.util.CglibUtil;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.bo.THealthSummaryDailyBO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyAddDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyDeleteDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailySearchDTO;
import com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyUpdateDTO;
import com.ljwx.modules.health.domain.entity.THealthSummaryDaily;
import com.ljwx.modules.health.domain.vo.THealthSummaryDailyVO;
import com.ljwx.modules.health.facade.ITHealthSummaryDailyFacade;
import com.ljwx.modules.health.service.ITHealthSummaryDailyService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 用户每日健康画像汇总表 门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.THealthSummaryDailyFacadeImpl
 * @CreateTime 2025-05-01 - 21:33:15
 */

@Service
@RequiredArgsConstructor
public class THealthSummaryDailyFacadeImpl implements ITHealthSummaryDailyFacade {

    @NonNull
    private ITHealthSummaryDailyService tHealthSummaryDailyService;

    @Override
    public RPage<THealthSummaryDailyVO> listTHealthSummaryDailyPage(PageQuery pageQuery, THealthSummaryDailySearchDTO tHealthSummaryDailySearchDTO) {
        THealthSummaryDailyBO tHealthSummaryDailyBO = CglibUtil.convertObj(tHealthSummaryDailySearchDTO, THealthSummaryDailyBO::new);
        IPage<THealthSummaryDaily> tHealthSummaryDailyIPage = tHealthSummaryDailyService.listTHealthSummaryDailyPage(pageQuery, tHealthSummaryDailyBO);
        return RPage.build(tHealthSummaryDailyIPage, THealthSummaryDailyVO::new);
    }

    @Override
    public THealthSummaryDailyVO get(Long id) {
        THealthSummaryDaily byId = tHealthSummaryDailyService.getById(id);
        return CglibUtil.convertObj(byId, THealthSummaryDailyVO::new);
    }

    @Override
    @Transactional
    public boolean add(THealthSummaryDailyAddDTO tHealthSummaryDailyAddDTO) {
        THealthSummaryDailyBO tHealthSummaryDailyBO = CglibUtil.convertObj(tHealthSummaryDailyAddDTO, THealthSummaryDailyBO::new);
        return tHealthSummaryDailyService.save(tHealthSummaryDailyBO);
    }

    @Override
    @Transactional
    public boolean update(THealthSummaryDailyUpdateDTO tHealthSummaryDailyUpdateDTO) {
        THealthSummaryDailyBO tHealthSummaryDailyBO = CglibUtil.convertObj(tHealthSummaryDailyUpdateDTO, THealthSummaryDailyBO::new);
        return tHealthSummaryDailyService.updateById(tHealthSummaryDailyBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(THealthSummaryDailyDeleteDTO tHealthSummaryDailyDeleteDTO) {
        THealthSummaryDailyBO tHealthSummaryDailyBO = CglibUtil.convertObj(tHealthSummaryDailyDeleteDTO, THealthSummaryDailyBO::new);
        return tHealthSummaryDailyService.removeBatchByIds(tHealthSummaryDailyBO.getIds(), true);
    }

}