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
import com.ljwx.modules.health.domain.bo.TUserHealthDataBO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataAddDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataDeleteDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataSearchDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataUpdateDTO;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.vo.TUserHealthDataVO;
import com.ljwx.modules.health.domain.vo.HealthDataPageVO;
import com.ljwx.modules.health.facade.ITUserHealthDataFacade;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.Map;
/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TUserHealthDataFacadeImpl
 * @CreateTime 2024-12-15 - 22:04:51
 */

@Service
@RequiredArgsConstructor
public class TUserHealthDataFacadeImpl implements ITUserHealthDataFacade {

    @NonNull
    private ITUserHealthDataService tUserHealthDataService;

    @Override
    public HealthDataPageVO<Map<String,Object>> listTUserHealthDataPage(PageQuery pageQuery, TUserHealthDataSearchDTO tUserHealthDataBO) {
        return tUserHealthDataService.listTUserHealthDataPage(pageQuery, tUserHealthDataBO);
    }

    @Override
    public TUserHealthDataVO get(Long id) {
        TUserHealthData byId = tUserHealthDataService.getById(id);
        return CglibUtil.convertObj(byId, TUserHealthDataVO::new);
    }

    @Override
    @Transactional
    public boolean add(TUserHealthDataAddDTO tUserHealthDataAddDTO) {
        TUserHealthDataBO tUserHealthDataBO = CglibUtil.convertObj(tUserHealthDataAddDTO, TUserHealthDataBO::new);
        return tUserHealthDataService.save(tUserHealthDataBO);
    }

    @Override
    @Transactional
    public boolean update(TUserHealthDataUpdateDTO tUserHealthDataUpdateDTO) {
        TUserHealthDataBO tUserHealthDataBO = CglibUtil.convertObj(tUserHealthDataUpdateDTO, TUserHealthDataBO::new);
        return tUserHealthDataService.updateById(tUserHealthDataBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TUserHealthDataDeleteDTO tUserHealthDataDeleteDTO) {
        TUserHealthDataBO tUserHealthDataBO = CglibUtil.convertObj(tUserHealthDataDeleteDTO, TUserHealthDataBO::new);
        return tUserHealthDataService.removeBatchByIds(tUserHealthDataBO.getIds(), true);
    }

}