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

package com.ljwx.modules.health.facade.impl;

import com.ljwx.modules.health.domain.bo.TAlertInfoBO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoAddDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoDeleteDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoSearchDTO;
import com.ljwx.modules.health.domain.dto.alert.info.TAlertInfoUpdateDTO;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.domain.vo.TAlertInfoVO;
import com.ljwx.modules.health.facade.ITAlertInfoFacade;
import com.ljwx.modules.health.service.ITAlertInfoService;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import org.springframework.stereotype.Service;
import lombok.NonNull;
import org.springframework.transaction.annotation.Transactional;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;

import lombok.RequiredArgsConstructor;

/**
 *  门面接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TAlertInfoFacadeImpl
 * @CreateTime 2024-10-27 - 20:37:23
 */

@Service
@RequiredArgsConstructor
public class TAlertInfoFacadeImpl implements ITAlertInfoFacade {

    @NonNull
    private ITAlertInfoService tAlertInfoService;
    
    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;

    @Override
    public RPage<TAlertInfoVO> listTAlertInfoPage(PageQuery pageQuery, TAlertInfoSearchDTO tAlertInfoSearchDTO) {
        TAlertInfoBO tAlertInfoBO = CglibUtil.convertObj(tAlertInfoSearchDTO, TAlertInfoBO::new);
        IPage<TAlertInfo> tAlertInfoIPage = tAlertInfoService.listTAlertInfoPage(pageQuery, tAlertInfoBO);
        
        // Convert to VO with orgName mapping
        IPage<TAlertInfoVO> voPage = tAlertInfoIPage.convert(entity -> {
            TAlertInfoVO vo = CglibUtil.convertObj(entity, TAlertInfoVO::new);
            // Set orgName from orgId lookup
            if (entity.getOrgId() != null) {
                try {
                    SysOrgUnits orgUnit = sysOrgUnitsService.getById(entity.getOrgId());
                    String orgName = orgUnit != null ? orgUnit.getName() : null;
                    vo.setOrgName(orgName);
                    System.out.println("🔄 TAlertInfo orgId->orgName: " + entity.getOrgId() + " -> " + orgName);
                } catch (Exception e) {
                    vo.setOrgName(null);
                    System.out.println("❌ TAlertInfo orgName lookup failed for orgId: " + entity.getOrgId() + ", error: " + e.getMessage());
                }
            }
            return vo;
        });
        
        return RPage.build(voPage);
    }

    @Override
    public TAlertInfoVO get(Long id) {
        TAlertInfo byId = tAlertInfoService.getById(id);
        TAlertInfoVO vo = CglibUtil.convertObj(byId, TAlertInfoVO::new);
        
        // Set orgName from orgId lookup
        if (byId != null && byId.getOrgId() != null) {
            try {
                SysOrgUnits orgUnit = sysOrgUnitsService.getById(byId.getOrgId());
                vo.setOrgName(orgUnit != null ? orgUnit.getName() : null);
            } catch (Exception e) {
                vo.setOrgName(null);
            }
        }
        
        return vo;
    }

    @Override
    @Transactional
    public boolean add(TAlertInfoAddDTO tAlertInfoAddDTO) {
        TAlertInfoBO tAlertInfoBO = CglibUtil.convertObj(tAlertInfoAddDTO, TAlertInfoBO::new);
        return tAlertInfoService.save(tAlertInfoBO);
    }

    @Override
    @Transactional
    public boolean update(TAlertInfoUpdateDTO tAlertInfoUpdateDTO) {
        TAlertInfoBO tAlertInfoBO = CglibUtil.convertObj(tAlertInfoUpdateDTO, TAlertInfoBO::new);
        return tAlertInfoService.updateById(tAlertInfoBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TAlertInfoDeleteDTO tAlertInfoDeleteDTO) {
        TAlertInfoBO tAlertInfoBO = CglibUtil.convertObj(tAlertInfoDeleteDTO, TAlertInfoBO::new);
        return tAlertInfoService.removeBatchByIds(tAlertInfoBO.getIds(), true);
    }

}