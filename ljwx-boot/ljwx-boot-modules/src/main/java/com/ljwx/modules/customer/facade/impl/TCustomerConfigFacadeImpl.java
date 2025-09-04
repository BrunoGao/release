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

package com.ljwx.modules.customer.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.bo.TCustomerConfigBO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigUpdateDTO;
import com.ljwx.modules.customer.domain.entity.TCustomerConfig;
import com.ljwx.modules.customer.domain.vo.TCustomerConfigVO;
import com.ljwx.modules.customer.facade.ITCustomerConfigFacade;
import com.ljwx.modules.customer.service.ITCustomerConfigService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.event.SysOrgUnitsChangeEvent;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.customer.facade.impl.TCustomerConfigFacadeImpl
 * @CreateTime 2024-12-29 - 15:33:30
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class TCustomerConfigFacadeImpl implements ITCustomerConfigFacade {

    @NonNull
    private ITCustomerConfigService tCustomerConfigService;
    
    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @NonNull
    private ApplicationEventPublisher eventPublisher;

    @Override
    public RPage<TCustomerConfigVO> listTCustomerConfigPage(PageQuery pageQuery, TCustomerConfigSearchDTO tCustomerConfigSearchDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigSearchDTO, TCustomerConfigBO::new);
        IPage<TCustomerConfig> tCustomerConfigIPage = tCustomerConfigService.listTCustomerConfigPage(pageQuery, tCustomerConfigBO);
        return RPage.build(tCustomerConfigIPage, TCustomerConfigVO::new);
    }

    @Override
    public TCustomerConfigVO get(Long id) {
        TCustomerConfig byId = tCustomerConfigService.getById(id);
        return CglibUtil.convertObj(byId, TCustomerConfigVO::new);
    }

    @Override
    @Transactional
    public boolean add(TCustomerConfigAddDTO tCustomerConfigAddDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigAddDTO, TCustomerConfigBO::new);
        
        // 处理字段映射：supportLicense -> isSupportLicense
        if (tCustomerConfigAddDTO.getSupportLicense() != null) {
            tCustomerConfigBO.setIsSupportLicense(tCustomerConfigAddDTO.getSupportLicense());
        }
        
        boolean result = tCustomerConfigService.save(tCustomerConfigBO);
        
        if (result && tCustomerConfigBO.getId() != null) {
            // 同步到 sys_org_units 表
            syncToSysOrgUnits(tCustomerConfigBO.getId(), tCustomerConfigBO.getCustomerName(), "CREATE");
        }
        
        return result;
    }

    @Override
    @Transactional
    public boolean update(TCustomerConfigUpdateDTO tCustomerConfigUpdateDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigUpdateDTO, TCustomerConfigBO::new);
        
        // DTO中已经是isSupportLicense字段，无需特殊映射
        
        boolean result = tCustomerConfigService.updateById(tCustomerConfigBO);
        
        if (result && tCustomerConfigBO.getId() != null) {
            // 同步到 sys_org_units 表
            syncToSysOrgUnits(tCustomerConfigBO.getId(), tCustomerConfigBO.getCustomerName(), "UPDATE");
        }
        
        return result;
    }

    @Override
    @Transactional
    public boolean batchDelete(TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigDeleteDTO, TCustomerConfigBO::new);
        
        // 在删除前先同步到 sys_org_units
        if (tCustomerConfigBO.getIds() != null) {
            for (Long id : tCustomerConfigBO.getIds()) {
                syncToSysOrgUnits(id, null, "DELETE");
            }
        }
        
        return tCustomerConfigService.removeBatchByIds(tCustomerConfigBO.getIds(), true);
    }
    
    /**
     * 同步租户配置到 sys_org_units 表并发布事件
     */
    private void syncToSysOrgUnits(Long customerId, String customerName, String operationType) {
        try {
            log.info("同步租户配置到sys_org_units: customerId={}, customerName={}, operation={}", 
                    customerId, customerName, operationType);
            
            SysOrgUnits orgUnit;
            
            if ("DELETE".equals(operationType)) {
                // 删除操作：标记为删除
                orgUnit = sysOrgUnitsService.getById(customerId);
                if (orgUnit != null) {
                    orgUnit.setIsDeleted(1);
                    sysOrgUnitsService.updateById(orgUnit);
                } else {
                    // 创建一个删除标记的组织单元
                    orgUnit = SysOrgUnits.builder()
                        .id(customerId)
                        .parentId(0L)
                        .name("已删除租户")
                        .code("deleted_" + customerId)
                        .level(1)
                        .ancestors("0")
                        .description("已删除的租户")
                        .sort(999)
                        .status("0")
                        .isDeleted(1)
                        .customerId(customerId)
                        .build();
                }
            } else {
                // 新增或更新操作
                orgUnit = sysOrgUnitsService.getById(customerId);
                if (orgUnit == null) {
                    // 创建新的组织单元（顶级租户）
                    orgUnit = SysOrgUnits.builder()
                        .id(customerId)
                        .parentId(0L) // 顶级租户的父ID为0
                        .name(customerName)
                        .code("tenant_" + customerId)
                        .level(1) // 顶级租户为第一级
                        .ancestors("0") // 祖先路径为"0"
                        .description("租户: " + customerName)
                        .sort(1)
                        .status("1") // 启用状态
                        .isDeleted(0)
                        .customerId(customerId)
                        .build();
                    sysOrgUnitsService.save(orgUnit);
                } else if (customerName != null && !customerName.equals(orgUnit.getName())) {
                    // 更新组织单元名称
                    orgUnit.setName(customerName);
                    orgUnit.setDescription("租户: " + customerName);
                    orgUnit.setIsDeleted(0); // 确保不是删除状态
                    sysOrgUnitsService.updateById(orgUnit);
                }
            }
            
            // 发布组织变更事件，触发 OrgUnitsChangeListener
            SysOrgUnitsChangeEvent event = new SysOrgUnitsChangeEvent(this, orgUnit, operationType);
            eventPublisher.publishEvent(event);
            
            log.info("成功发布组织变更事件: customerId={}, operation={}", customerId, operationType);
            
        } catch (Exception e) {
            log.error("同步租户配置到sys_org_units失败: customerId={}, operation={}", customerId, operationType, e);
            // 不抛出异常，避免影响主业务流程
        }
    }

}