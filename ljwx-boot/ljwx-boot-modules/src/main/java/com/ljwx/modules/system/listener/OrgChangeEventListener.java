package com.ljwx.modules.system.listener;

import com.ljwx.modules.system.event.OrgDeleteEvent;
import com.ljwx.modules.system.event.OrgNameChangeEvent;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 组织变更事件监听器
 * 用于同步用户表中的组织冗余信息
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-01-26
 */
@Component
@Slf4j
public class OrgChangeEventListener {
    
    @Autowired
    private ISysUserService userService;
    
    /**
     * 处理组织名称变更事件
     */
    @EventListener
    @Async
    public void handleOrgNameChange(OrgNameChangeEvent event) {
        try {
            log.info("🔄 开始处理组织名称变更事件: orgId={}, {} -> {}", 
                    event.getOrgId(), event.getOldOrgName(), event.getNewOrgName());
            
            // 同步更新所有该组织用户的org_name
            int updatedCount = userService.updateOrgNameByOrgId(event.getOrgId(), event.getNewOrgName());
            
            log.info("✅ 组织名称同步完成: orgId={}, 更新用户数={}", 
                    event.getOrgId(), updatedCount);
                    
        } catch (Exception e) {
            log.error("❌ 处理组织名称变更事件失败: orgId={}, error={}", 
                    event.getOrgId(), e.getMessage(), e);
        }
    }
    
    /**
     * 处理组织删除事件
     */
    @EventListener  
    @Async
    public void handleOrgDelete(OrgDeleteEvent event) {
        try {
            log.info("🗑️ 开始处理组织删除事件: orgId={}, orgName={}", 
                    event.getOrgId(), event.getOrgName());
            
            // 清理被删除组织的用户关联
            int clearedCount = userService.clearOrgInfoByOrgId(event.getOrgId());
            
            log.info("✅ 组织用户关联清理完成: orgId={}, 清理用户数={}", 
                    event.getOrgId(), clearedCount);
                    
        } catch (Exception e) {
            log.error("❌ 处理组织删除事件失败: orgId={}, error={}", 
                    event.getOrgId(), e.getMessage(), e);
        }
    }
}