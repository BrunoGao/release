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
import com.ljwx.modules.health.domain.bo.TDeviceInfoBO;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.repository.mapper.TDeviceInfoMapper;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.system.service.ISysUserService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceInfoServiceImpl
 * @CreateTime 2024-12-14 - 21:31:16
 */

@Service
public class TDeviceInfoServiceImpl extends ServiceImpl<TDeviceInfoMapper, TDeviceInfo> implements ITDeviceInfoService {


    @Autowired
    private ISysUserService sysUserService;


    @Override
    public IPage<TDeviceInfo> listTDeviceInfoPage(PageQuery pageQuery, TDeviceInfoBO tDeviceInfoBO) {
        // 使用自定义查询，直接包含用户名关联
        IPage<TDeviceInfo> page = pageQuery.buildPage();
        return baseMapper.listDeviceInfoWithUserName(page, tDeviceInfoBO);
    }
    
    @Override
    public TDeviceInfo getBySerialNumber(String serialNumber) {
        return this.getOne(new LambdaQueryWrapper<TDeviceInfo>()
                .eq(TDeviceInfo::getSerialNumber, serialNumber));
    }

}

