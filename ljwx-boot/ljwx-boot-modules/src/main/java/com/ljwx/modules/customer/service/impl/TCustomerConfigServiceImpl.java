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

package com.ljwx.modules.customer.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.customer.domain.bo.TCustomerConfigBO;
import com.ljwx.modules.customer.domain.entity.TCustomerConfig;
import com.ljwx.modules.customer.repository.mapper.TCustomerConfigMapper;
import com.ljwx.modules.customer.service.ITCustomerConfigService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.customer.service.impl.TCustomerConfigServiceImpl
 * @CreateTime 2024-12-29 - 15:33:30
 */

@Service
public class TCustomerConfigServiceImpl extends ServiceImpl<TCustomerConfigMapper, TCustomerConfig> implements ITCustomerConfigService {

    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    @Override
    public IPage<TCustomerConfig> listTCustomerConfigPage(PageQuery pageQuery, TCustomerConfigBO tCustomerConfigBO) {
        LambdaQueryWrapper<TCustomerConfig> queryWrapper = new LambdaQueryWrapper<TCustomerConfig>()
                .eq(ObjectUtils.isNotEmpty(tCustomerConfigBO.getId()), TCustomerConfig::getId, tCustomerConfigBO.getId());
        
        // 简化查询，移除租户逻辑暂时 - 暂时注释掉getCustomerName调用避免编译错误
        // if (ObjectUtils.isNotEmpty(tCustomerConfigBO.getCustomerName())) {
        //     queryWrapper.like(TCustomerConfig::getCustomerName, tCustomerConfigBO.getCustomerName());
        // }
        
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean save(TCustomerConfig entity) {
        // 设置必需字段的默认值
        if (entity.getLicenseKey() == null) {
            entity.setLicenseKey(0);
        }
        if (entity.getIsSupportLicense() == null) {
            entity.setIsSupportLicense(false);
        }
        if (entity.getCustomerId() == null) {
            entity.setCustomerId(0L);
        }
        if (entity.getCustomerName() == null) {
            entity.setCustomerName("");
        }
        
        boolean result = super.save(entity);
        
        if (result && entity.getId() != null) {
            // 检查是否已存在对应的组织机构，避免重复创建
            SysOrgUnits existingOrg = sysOrgUnitsService.getById(entity.getId());
            if (existingOrg == null) {
                // 同步创建顶级组织机构
                SysOrgUnits orgUnit = new SysOrgUnits();
                orgUnit.setId(entity.getId());
                orgUnit.setName(entity.getCustomerName());
                orgUnit.setParentId(0L);
                orgUnit.setAncestors("0");
                orgUnit.setSort(1);
                orgUnit.setStatus("1");
                orgUnit.setIsDeleted(0);
                orgUnit.setCustomerId(entity.getId());
                
                sysOrgUnitsService.save(orgUnit);
                
                // 注意：这里不发布事件，因为SysOrgUnitsServiceImpl.save()方法已经会发布CREATE事件
                // 避免重复触发监听器
            }
        }
        
        return result;
    }

}

