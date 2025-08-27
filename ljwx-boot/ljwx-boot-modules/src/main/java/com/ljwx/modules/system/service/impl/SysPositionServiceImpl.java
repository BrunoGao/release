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

package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysPositionBO;
import com.ljwx.modules.system.domain.entity.SysPosition;
import com.ljwx.modules.system.repository.mapper.SysPositionMapper;
import com.ljwx.modules.system.service.ISysPositionService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 岗位管理 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.SysPositionServiceImpl
 * @CreateTime 2024-06-27 - 22:03:29
 */

@Service
public class SysPositionServiceImpl extends ServiceImpl<SysPositionMapper, SysPosition> implements ISysPositionService {

    @Override
    public IPage<SysPosition> listSysPositionPage(PageQuery pageQuery, SysPositionBO sysPositionBO) {
        LambdaQueryWrapper<SysPosition> queryWrapper = new LambdaQueryWrapper<SysPosition>()
                .like(ObjectUtils.isNotEmpty(sysPositionBO.getName()), SysPosition::getName, sysPositionBO.getName())
                .eq(ObjectUtils.isNotEmpty(sysPositionBO.getStatus()), SysPosition::getStatus, sysPositionBO.getStatus());
                
        // 部门过滤（基于orgId）
        if (sysPositionBO.getOrgIds() != null && !sysPositionBO.getOrgIds().isEmpty()) {
            queryWrapper.in(SysPosition::getOrgId, sysPositionBO.getOrgIds());
        } else if (sysPositionBO.getOrgId() != null && sysPositionBO.getOrgId() != 0L) {
            queryWrapper.eq(SysPosition::getOrgId, sysPositionBO.getOrgId());
        }
        
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

    @Override
    public List<SysPositionBO> queryAllPositionList(Long orgId) {   
        LambdaQueryWrapper<SysPosition> queryWrapper = new LambdaQueryWrapper<SysPosition>()
                .eq(SysPosition::getOrgId, orgId)
                .orderByAsc(SysPosition::getSort);
        return CglibUtil.convertList(baseMapper.selectList(queryWrapper), SysPositionBO::new);
    }

    @Override
    public List<SysPositionBO> queryAllPositionList() {
        LambdaQueryWrapper<SysPosition> queryWrapper = new LambdaQueryWrapper<SysPosition>()
                .orderByAsc(SysPosition::getSort);
        return CglibUtil.convertList(baseMapper.selectList(queryWrapper), SysPositionBO::new);
    }

    @Override
    public List<SysPositionBO> queryAllPositionListByCustomerIds(List<Long> customerIds) {
        LambdaQueryWrapper<SysPosition> queryWrapper = new LambdaQueryWrapper<SysPosition>();
        
        if (customerIds != null && !customerIds.isEmpty()) {
            queryWrapper.in(SysPosition::getCustomerId, customerIds);
        }
        
        queryWrapper.orderByAsc(SysPosition::getSort);
        return CglibUtil.convertList(baseMapper.selectList(queryWrapper), SysPositionBO::new);
    }
}

