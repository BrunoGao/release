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
import com.ljwx.modules.customer.domain.bo.TInterfaceBO;
import com.ljwx.modules.customer.domain.entity.TInterface;
import com.ljwx.modules.customer.repository.mapper.TInterfaceMapper;
import com.ljwx.modules.customer.service.ITInterfaceService;
import org.springframework.stereotype.Service;
import org.apache.commons.lang3.ObjectUtils;
/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.customer.service.impl.TInterfaceServiceImpl
 * @CreateTime 2024-12-29 - 15:33:49
 */

@Service
public class TInterfaceServiceImpl extends ServiceImpl<TInterfaceMapper, TInterface> implements ITInterfaceService {

    @Override
    public IPage<TInterface> listTInterfacePage(PageQuery pageQuery, TInterfaceBO tInterfaceBO) {
        Long customerId = tInterfaceBO.getCustomerId();
        LambdaQueryWrapper<TInterface> queryWrapper = new LambdaQueryWrapper<TInterface>()
        .eq(ObjectUtils.isNotEmpty(tInterfaceBO.getName()), TInterface::getName, tInterfaceBO.getName())
        .eq(ObjectUtils.isNotEmpty(customerId), TInterface::getCustomerId, customerId).orderByDesc(TInterface::getCreateTime);
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

