package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 用户组织数据一致性检查器
 * 定时检查并修复用户表中组织信息的数据一致性
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-01-26
 */
@Component
@Slf4j
public class UserOrgConsistencyChecker {
    
    @Autowired
    private ISysUserService userService;
    
    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;
    
    /**
     * 用户组织一致性检查任务
     * 每天凌晨2点执行，检查用户表中org_name与org表是否一致
     */
    @Scheduled(cron = "0 0 2 * * ?")
    public void checkUserOrgConsistency() {
        log.info("🔍 开始执行用户组织数据一致性检查任务");
        
        try {
            // 查询所有有组织ID但组织名称可能不一致的用户
            List<SysUser> inconsistentUsers = findInconsistentOrgUsers();
            
            if (inconsistentUsers.isEmpty()) {
                log.info("✅ 用户组织数据一致性检查完成，未发现不一致数据");
                return;
            }
            
            log.info("⚠️ 发现{}个用户的组织信息不一致，开始修复", inconsistentUsers.size());
            
            int repairedCount = 0;
            int failedCount = 0;
            
            for (SysUser user : inconsistentUsers) {
                try {
                    if (user.getOrgId() != null) {
                        SysOrgUnits org = sysOrgUnitsService.getById(user.getOrgId());
                        if (org != null) {
                            if (!org.getName().equals(user.getOrgName())) {
                                user.setOrgName(org.getName());
                                boolean updated = userService.updateById(user);
                                
                                if (updated) {
                                    repairedCount++;
                                    log.info("🔧 修复用户{}的组织名称不一致: userId={}, orgId={}, {} -> {}", 
                                            user.getUserName(), user.getId(), user.getOrgId(), 
                                            user.getOrgName(), org.getName());
                                } else {
                                    failedCount++;
                                    log.error("❌ 修复用户{}的组织名称失败", user.getUserName());
                                }
                            }
                        } else {
                            // 组织不存在，清理用户的组织信息
                            user.setOrgId(null);
                            user.setOrgName(null);
                            boolean updated = userService.updateById(user);
                            
                            if (updated) {
                                repairedCount++;
                                log.info("🗑️ 清理用户{}的无效组织信息: userId={}, orgId={}", 
                                        user.getUserName(), user.getId(), user.getOrgId());
                            } else {
                                failedCount++;
                                log.error("❌ 清理用户{}的无效组织信息失败", user.getUserName());
                            }
                        }
                    }
                } catch (Exception e) {
                    failedCount++;
                    log.error("❌ 处理用户{}的组织信息时发生异常: {}", user.getUserName(), e.getMessage(), e);
                }
            }
            
            log.info("✅ 用户组织数据一致性检查任务完成: 总检查={}个, 修复成功={}个, 修复失败={}个", 
                    inconsistentUsers.size(), repairedCount, failedCount);
                    
        } catch (Exception e) {
            log.error("❌ 用户组织数据一致性检查任务执行失败: {}", e.getMessage(), e);
        }
    }
    
    /**
     * 查找组织信息不一致的用户
     */
    public List<SysUser> findInconsistentOrgUsers() {
        try {
            // 查询所有有组织ID的用户
            QueryWrapper<SysUser> wrapper = new QueryWrapper<>();
            wrapper.isNotNull("org_id")
                   .ne("is_deleted", 1);
            
            return userService.list(wrapper);
        } catch (Exception e) {
            log.error("❌ 查询不一致用户列表失败: {}", e.getMessage(), e);
            return List.of();
        }
    }
    
    /**
     * 手动触发一致性检查（用于测试或紧急修复）
     */
    public void manualConsistencyCheck() {
        log.info("🔧 手动触发用户组织数据一致性检查");
        checkUserOrgConsistency();
    }
}