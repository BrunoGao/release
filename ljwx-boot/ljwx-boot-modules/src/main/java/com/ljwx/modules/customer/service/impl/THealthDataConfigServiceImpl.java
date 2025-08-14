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

package com.ljwx.modules.customer.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.customer.domain.bo.THealthDataConfigBO;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.repository.mapper.THealthDataConfigMapper;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.customer.service.impl.THealthDataConfigServiceImpl
 * @CreateTime 2024-12-29 - 15:02:31
 */

@Service
@RequiredArgsConstructor 
public class THealthDataConfigServiceImpl extends ServiceImpl<THealthDataConfigMapper, THealthDataConfig> implements ITHealthDataConfigService {

    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;

    @Override
    public IPage<THealthDataConfig> listTHealthDataConfigPage(PageQuery pageQuery, THealthDataConfigBO tHealthDataConfigBO) {

        Long customerId = tHealthDataConfigBO.getCustomerId();
        System.out.println("customerId: " + customerId);
        Long firstParent = sysOrgUnitsService.getFirstParent(customerId);
        System.out.println("firstParent: " + firstParent);

        LambdaQueryWrapper<THealthDataConfig> queryWrapper = new LambdaQueryWrapper<THealthDataConfig>()
            .eq(ObjectUtils.isNotEmpty(firstParent), THealthDataConfig::getCustomerId, firstParent)
            .eq(ObjectUtils.isNotEmpty(tHealthDataConfigBO.getDataType()), THealthDataConfig::getDataType, tHealthDataConfigBO.getDataType())
            .orderByDesc(THealthDataConfig::getCreateTime);
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

