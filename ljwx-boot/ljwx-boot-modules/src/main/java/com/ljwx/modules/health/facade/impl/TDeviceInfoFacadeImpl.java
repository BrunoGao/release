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

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.bo.TDeviceInfoBO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoAddDTO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoDeleteDTO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoSearchDTO;
import com.ljwx.modules.health.domain.dto.device.info.TDeviceInfoUpdateDTO;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.vo.TDeviceInfoVO;
import com.ljwx.modules.health.facade.ITDeviceInfoFacade;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TDeviceInfoFacadeImpl
 * @CreateTime 2024-12-14 - 21:31:16
 */

@Service
@RequiredArgsConstructor
public class TDeviceInfoFacadeImpl implements ITDeviceInfoFacade {

    @NonNull
    private ITDeviceInfoService tDeviceInfoService;
    
    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;

    @Override
    public RPage<TDeviceInfoVO> listTDeviceInfoPage(PageQuery pageQuery, TDeviceInfoSearchDTO tDeviceInfoSearchDTO) {
       TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoSearchDTO, TDeviceInfoBO::new);
       // #确保userId正确转换为userIdStr字段
       tDeviceInfoBO.setUserIdStr(tDeviceInfoSearchDTO.getUserId());
       
       // #处理前端参数映射: orgId 字符串转Long
       if (tDeviceInfoSearchDTO.getOrgId() != null && !tDeviceInfoSearchDTO.getOrgId().isEmpty()) {
           try {
               tDeviceInfoBO.setOrgId(Long.parseLong(tDeviceInfoSearchDTO.getOrgId()));
           } catch (NumberFormatException e) {
               tDeviceInfoBO.setOrgId(null);
           }
       }
       
       System.out.println("🔄 参数转换 - userId: " + tDeviceInfoSearchDTO.getUserId() + " -> userIdStr: " + tDeviceInfoBO.getUserIdStr());
       System.out.println("🔄 参数转换 - orgId: " + tDeviceInfoSearchDTO.getOrgId() + " -> " + tDeviceInfoBO.getOrgId());
        IPage<TDeviceInfo> tDeviceInfoIPage = tDeviceInfoService.listTDeviceInfoPage(pageQuery, tDeviceInfoBO);
        
        // Convert to VO with orgName mapping
        IPage<TDeviceInfoVO> voPage = tDeviceInfoIPage.convert(entity -> {
            TDeviceInfoVO vo = CglibUtil.convertObj(entity, TDeviceInfoVO::new);
            
            // 🔧 确保userName字段被正确复制
            vo.setUserName(entity.getUserName());
            System.out.println("🔄 TDeviceInfo userName: " + entity.getUserName() + " -> VO userName: " + vo.getUserName());
            
            // Set orgName from orgId lookup
            if (entity.getOrgId() != null) {
                try {
                    SysOrgUnits orgUnit = sysOrgUnitsService.getById(entity.getOrgId());
                    String orgName = orgUnit != null ? orgUnit.getName() : null;
                    vo.setOrgName(orgName);
                    System.out.println("🔄 TDeviceInfo orgId->orgName: " + entity.getOrgId() + " -> " + orgName);
                } catch (Exception e) {
                    vo.setOrgName(null);
                    System.out.println("❌ TDeviceInfo orgName lookup failed for orgId: " + entity.getOrgId() + ", error: " + e.getMessage());
                }
            }
            return vo;
        });
        
        return RPage.build(voPage);
    }

    @Override
    public TDeviceInfoVO get(Long id) {
        TDeviceInfo byId = tDeviceInfoService.getById(id);
        return CglibUtil.convertObj(byId, TDeviceInfoVO::new);
    }

    @Override
    @Transactional
    public boolean add(TDeviceInfoAddDTO tDeviceInfoAddDTO) {
        TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoAddDTO, TDeviceInfoBO::new);
        return tDeviceInfoService.save(tDeviceInfoBO);
    }

    @Override
    @Transactional
    public boolean update(TDeviceInfoUpdateDTO tDeviceInfoUpdateDTO) {
        TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoUpdateDTO, TDeviceInfoBO::new);
        return tDeviceInfoService.updateById(tDeviceInfoBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(TDeviceInfoDeleteDTO tDeviceInfoDeleteDTO) {
        TDeviceInfoBO tDeviceInfoBO = CglibUtil.convertObj(tDeviceInfoDeleteDTO, TDeviceInfoBO::new);
        return tDeviceInfoService.removeBatchByIds(tDeviceInfoBO.getIds(), true);
    }

}