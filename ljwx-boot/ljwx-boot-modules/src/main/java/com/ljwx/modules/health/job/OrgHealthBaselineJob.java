package com.ljwx.modules.health.job;

import com.ljwx.modules.health.service.UnifiedHealthBaselineService;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import lombok.extern.slf4j.Slf4j;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 组织健康基线生成定时作业 - 集成到mon_scheduler系统
 * 使用统一健康基线服务优化基线生成逻辑
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.job.OrgHealthBaselineJob
 * @CreateTime 2025-01-26
 * @UpdateTime 2025-01-26 - 集成UnifiedHealthBaselineService
 */
@Slf4j
@Component
public class OrgHealthBaselineJob implements Job {

    @Autowired
    private UnifiedHealthBaselineService unifiedHealthBaselineService;
    
    @Autowired(required = false)
    private ISysOrgUnitsService sysOrgUnitsService;
    
    private final ExecutorService executorService = Executors.newFixedThreadPool(5);

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        String jobName = context.getJobDetail().getKey().getName();
        log.info("🚀 开始执行统一组织健康基线生成作业: {}", jobName);
        
        try {
            long startTime = System.currentTimeMillis();
            int totalOrgsProcessed = 0;
            int successfulOrgs = 0;
            
            // 获取所有活跃组织
            List<Long> orgIds = getActiveOrganizations();
            
            if (orgIds.isEmpty()) {
                log.warn("⚠️ 未找到活跃组织，跳过组织基线生成");
                return;
            }
            
            log.info("📊 开始处理{}个组织的健康基线生成", orgIds.size());
            
            // 并行处理组织基线生成
            CompletableFuture<?>[] futures = orgIds.stream()
                .map(orgId -> CompletableFuture.runAsync(() -> {
                    try {
                        // 使用统一健康基线服务生成组织基线
                        unifiedHealthBaselineService.generateUnifiedBaseline(
                            "org", orgId, null, 90, null);
                        
                        synchronized (this) {
                            log.debug("✅ 组织{}基线生成成功", orgId);
                        }
                    } catch (Exception e) {
                        synchronized (this) {
                            log.error("❌ 组织{}基线生成失败: {}", orgId, e.getMessage(), e);
                        }
                    }
                }, executorService))
                .toArray(CompletableFuture[]::new);
            
            // 等待所有任务完成
            CompletableFuture.allOf(futures).join();
            
            // 统计处理结果
            totalOrgsProcessed = orgIds.size();
            successfulOrgs = (int) orgIds.stream()
                .mapToLong(orgId -> {
                    try {
                        // 检查基线是否生成成功
                        return unifiedHealthBaselineService.queryBaselines(
                            "org", orgId, null, null).size() > 0 ? 1 : 0;
                    } catch (Exception e) {
                        return 0;
                    }
                }).sum();
            
            long executionTime = System.currentTimeMillis() - startTime;
            
            log.info("✅ 统一组织健康基线生成作业完成: {}", jobName);
            log.info("📈 处理统计: 总组织数={}, 成功生成={}, 失败数={}, 耗时={}ms", 
                totalOrgsProcessed, successfulOrgs, totalOrgsProcessed - successfulOrgs, executionTime);
            
        } catch (Exception e) {
            log.error("❌ 统一组织健康基线生成作业失败: {}, 错误: {}", jobName, e.getMessage(), e);
            throw new JobExecutionException("统一组织健康基线生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 获取所有活跃组织ID列表
     */
    private List<Long> getActiveOrganizations() {
        try {
            if (sysOrgUnitsService != null) {
                // 使用组织服务获取活跃组织
                return sysOrgUnitsService.list().stream()
                    .filter(org -> org != null && (org.getIsDeleted() == null || org.getIsDeleted() == 0))
                    .map(org -> org.getId())
                    .toList();
            } else {
                // 如果组织服务不可用，返回默认组织ID列表
                log.warn("⚠️ 组织服务不可用，使用默认组织ID列表");
                return List.of(1L, 2L, 3L); // 可根据实际情况调整
            }
        } catch (Exception e) {
            log.error("❌ 获取活跃组织列表失败: {}", e.getMessage());
            // 返回默认组织ID列表作为fallback
            return List.of(1L);
        }
    }
    
    /**
     * 关闭线程池资源
     */
    public void shutdown() {
        if (executorService != null && !executorService.isShutdown()) {
            executorService.shutdown();
        }
    }
}