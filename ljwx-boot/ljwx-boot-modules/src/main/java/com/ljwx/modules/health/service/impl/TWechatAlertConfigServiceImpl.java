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

package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.bo.TWechatAlertConfigBO;
import com.ljwx.modules.health.domain.entity.TWechatAlertConfig;
import com.ljwx.modules.health.repository.mapper.TWechatAlertConfigMapper;
import com.ljwx.modules.health.service.ITWechatAlertConfigService;
import org.springframework.stereotype.Service;

/**
 * Table to store WeChat alert configuration Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TWechatAlertConfigServiceImpl
 * @CreateTime 2025-01-02 - 13:17:05
 */

@Service
public class TWechatAlertConfigServiceImpl extends ServiceImpl<TWechatAlertConfigMapper, TWechatAlertConfig> implements ITWechatAlertConfigService {

    @Override
    public IPage<TWechatAlertConfig> listTWechatAlertConfigPage(PageQuery pageQuery, TWechatAlertConfigBO tWechatAlertConfigBO) {
        LambdaQueryWrapper<TWechatAlertConfig> queryWrapper = new LambdaQueryWrapper<TWechatAlertConfig>();
        
        // 数据权限过滤
        if (tWechatAlertConfigBO.getCustomerId() != null) {
            if (tWechatAlertConfigBO.getCustomerId() == 0L) {
                // admin用户，查看所有数据，无需过滤
            } else {
                // 租户用户，查看admin创建的(customer_id=0)和自己租户的数据
                queryWrapper.and(wrapper -> 
                    wrapper.eq(TWechatAlertConfig::getCustomerId, 0L)
                           .or()
                           .eq(TWechatAlertConfig::getCustomerId, tWechatAlertConfigBO.getCustomerId())
                );
            }
        }
        
        // 其他条件
        queryWrapper.eq(tWechatAlertConfigBO.getType() != null, TWechatAlertConfig::getType, tWechatAlertConfigBO.getType())
                   .eq(tWechatAlertConfigBO.getEnabled() != null, TWechatAlertConfig::getEnabled, tWechatAlertConfigBO.getEnabled());
                   
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

