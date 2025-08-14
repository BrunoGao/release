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

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.bo.TDeviceMessageDepartmentBO;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDepartment;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageDepartmentMapper;
import com.ljwx.modules.health.service.ITDeviceMessageDepartmentService;
import org.springframework.stereotype.Service;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.device.service.impl.TDeviceMessageDepartmentServiceImpl
 * @CreateTime 2025-03-03 - 20:20:27
 */

@Service
public class TDeviceMessageDepartmentServiceImpl extends ServiceImpl<TDeviceMessageDepartmentMapper, TDeviceMessageDepartment> implements ITDeviceMessageDepartmentService {

    @Override
    public IPage<TDeviceMessageDepartment> listTDeviceMessageDepartmentPage(PageQuery pageQuery, TDeviceMessageDepartmentBO tDeviceMessageDepartmentBO) {
        LambdaQueryWrapper<TDeviceMessageDepartment> queryWrapper = new LambdaQueryWrapper<TDeviceMessageDepartment>();
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

}

