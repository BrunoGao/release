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

package com.ljwx.modules.health.service.impl;

import com.ljwx.modules.health.domain.bo.TDeviceConfigBO;
import com.ljwx.modules.health.domain.entity.TDeviceConfig;
import com.ljwx.modules.health.repository.mapper.TDeviceConfigMapper;
import com.ljwx.modules.health.service.ITDeviceConfigService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.infrastructure.page.PageQuery;
import org.apache.commons.lang3.ObjectUtils;

/**
 *  Service 服务接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceConfigServiceImpl
 * @CreateTime 2024-10-21 - 19:44:31
 */

@Service
public class TDeviceConfigServiceImpl extends ServiceImpl<TDeviceConfigMapper, TDeviceConfig> implements ITDeviceConfigService {

    @Override
    public IPage<TDeviceConfig> listTDeviceConfigPage(PageQuery pageQuery, TDeviceConfigBO tDeviceConfigBO) {
        LambdaQueryWrapper<TDeviceConfig> queryWrapper = new LambdaQueryWrapper<TDeviceConfig>()
            .eq(ObjectUtils.isNotEmpty(tDeviceConfigBO.getLogo()), TDeviceConfig::getLogo, tDeviceConfigBO.getLogo());
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

