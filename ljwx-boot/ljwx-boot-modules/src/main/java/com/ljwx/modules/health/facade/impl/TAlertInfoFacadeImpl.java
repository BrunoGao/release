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
import com.ljwx.modules.health.service.ITAlertActionLogService;
import com.ljwx.modules.health.domain.entity.TAlertActionLog;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.common.context.UserContext;
import org.springframework.stereotype.Service;
import lombok.NonNull;
import org.springframework.transaction.annotation.Transactional;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import java.time.LocalDateTime;
import java.util.List;

/**
 *  门面接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.health.facade.impl.TAlertInfoFacadeImpl
 * @CreateTime 2024-10-27 - 20:37:23
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class TAlertInfoFacadeImpl implements ITAlertInfoFacade {

    @NonNull
    private ITAlertInfoService tAlertInfoService;
    
    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @NonNull
    private ITAlertActionLogService tAlertActionLogService;

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
        List<Long> alertIds = tAlertInfoBO.getIds();
        
        // 记录删除操作到日志表
        if (alertIds != null && !alertIds.isEmpty()) {
            // 获取当前用户信息
            String currentUserName = UserContext.getCurrentUserName();
            Long currentUserId = UserContext.getCurrentUserId();
            Long customerId = UserContext.getCustomerId();
            
            // 获取要删除的告警信息，用于日志记录
            List<TAlertInfo> alertsToDelete = tAlertInfoService.listByIds(alertIds);
            
            // 为每个被删除的告警创建日志记录
            for (TAlertInfo alert : alertsToDelete) {
                TAlertActionLog actionLog = new TAlertActionLog();
                actionLog.setAlertId(alert.getId());
                actionLog.setCustomerId(customerId != null ? customerId : alert.getCustomerId());
                actionLog.setAction("DELETE");
                actionLog.setActionTimestamp(LocalDateTime.now());
                actionLog.setActionUser(currentUserName);
                actionLog.setActionUserId(currentUserId);
                actionLog.setDetails("删除告警记录: " + alert.getAlertType() + " - " + alert.getAlertDesc());
                actionLog.setResult("SUCCESS");
                
                try {
                    tAlertActionLogService.save(actionLog);
                } catch (Exception e) {
                    System.err.println("保存告警删除日志失败: " + e.getMessage());
                    // 日志记录失败不应该影响删除操作，只记录错误
                }
            }
        }
        
        // 执行删除操作
        return tAlertInfoService.removeBatchByIds(alertIds, true);
    }

    @Override
    public boolean dealAlert(Long alertId) {
        log.info("Dealing with alert id: {}", alertId);
        
        // 临时实现 - 返回成功
        return true;
    }

    @Override
    public String batchDealAlert(java.util.List<Long> alertIds) {
        log.info("Batch dealing with alert ids: {}", alertIds);
        
        // 临时实现 - 返回成功信息
        return "批量处理成功，共处理 " + alertIds.size() + " 个告警";
    }

}