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
import lombok.extern.slf4j.Slf4j;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.customer.service.impl.TCustomerConfigServiceImpl
 * @CreateTime 2024-12-29 - 15:33:30
 */

@Slf4j
@Service
public class TCustomerConfigServiceImpl extends ServiceImpl<TCustomerConfigMapper, TCustomerConfig> implements ITCustomerConfigService {

    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @Autowired
    private ApplicationEventPublisher eventPublisher;

    @Override
    public IPage<TCustomerConfig> listTCustomerConfigPage(PageQuery pageQuery, TCustomerConfigBO tCustomerConfigBO) {
        log.info("查询t_customer_config参数: id={}, customerId={}, customerName={}", 
                tCustomerConfigBO.getId(), tCustomerConfigBO.getCustomerId(), tCustomerConfigBO.getCustomerName());
        
        LambdaQueryWrapper<TCustomerConfig> queryWrapper = new LambdaQueryWrapper<TCustomerConfig>()
                .eq(ObjectUtils.isNotEmpty(tCustomerConfigBO.getId()) && tCustomerConfigBO.getId() > 0, 
                    TCustomerConfig::getId, tCustomerConfigBO.getId());
        
        // URL参数customerId是顶级部门ID，应该按customer_id字段查询
        if (ObjectUtils.isNotEmpty(tCustomerConfigBO.getCustomerId())) {
            log.info("按customer_id查询: {}", tCustomerConfigBO.getCustomerId());
            queryWrapper.eq(TCustomerConfig::getCustomerId, tCustomerConfigBO.getCustomerId());
        }
        
        if (ObjectUtils.isNotEmpty(tCustomerConfigBO.getCustomerName())) {
            queryWrapper.like(TCustomerConfig::getCustomerName, tCustomerConfigBO.getCustomerName());
        }
        
        IPage<TCustomerConfig> result = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
        log.info("查询结果: total={}, records={}", result.getTotal(), result.getRecords().size());
        
        return result;
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
        if (entity.getCustomerName() == null) {
            entity.setCustomerName("");
        }
        
        // 创建顶级部门作为customer的根组织
        SysOrgUnits topOrg = new SysOrgUnits();
        topOrg.setName(entity.getCustomerName());
        topOrg.setParentId(0L);
        topOrg.setAncestors("0");
        topOrg.setSort(1);
        topOrg.setStatus("1");
        topOrg.setIsDeleted(0);
        
        // 先保存顶级部门，获取生成的ID
        boolean orgSaved = sysOrgUnitsService.save(topOrg);
        if (!orgSaved) {
            throw new RuntimeException("创建顶级部门失败");
        }
        
        Long customerId = topOrg.getId();
        
        // 更新部门的customer_id为自己的ID（标识这是顶级customer部门）
        topOrg.setCustomerId(customerId);
        sysOrgUnitsService.updateById(topOrg);
        
        // 设置customer配置的customer_id指向顶级部门
        entity.setCustomerId(customerId);
        
        // 保存customer配置
        boolean result = super.save(entity);
        
        if (!result) {
            throw new RuntimeException("保存customer配置失败");
        }
        
        return result;
    }

}

