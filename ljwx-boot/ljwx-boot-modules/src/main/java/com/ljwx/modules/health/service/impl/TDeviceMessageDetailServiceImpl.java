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
import com.ljwx.modules.health.domain.bo.TDeviceMessageDetailBO;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetail;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageDetailMapper;
import com.ljwx.modules.health.service.ITDeviceMessageDetailService;
import org.springframework.stereotype.Service;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceMessageDetailServiceImpl
 * @CreateTime 2025-03-05 - 19:57:37
 */

@Service
public class TDeviceMessageDetailServiceImpl extends ServiceImpl<TDeviceMessageDetailMapper, TDeviceMessageDetail> implements ITDeviceMessageDetailService {

    @Override
    public IPage<TDeviceMessageDetail> listTDeviceMessageDetailPage(PageQuery pageQuery, TDeviceMessageDetailBO tDeviceMessageDetailBO) {
        LambdaQueryWrapper<TDeviceMessageDetail> queryWrapper = new LambdaQueryWrapper<TDeviceMessageDetail>();
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

