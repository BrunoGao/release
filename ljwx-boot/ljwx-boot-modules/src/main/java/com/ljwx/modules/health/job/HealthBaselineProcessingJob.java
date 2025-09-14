package com.ljwx.modules.health.job;

import com.ljwx.modules.health.service.UnifiedHealthProcessingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.quartz.QuartzJobBean;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 健康基线生成任务
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-09-13
 */
@Slf4j
@Component
public class HealthBaselineProcessingJob extends QuartzJobBean {

    @Autowired
    private UnifiedHealthProcessingService unifiedHealthProcessingService;

    @Override
    protected void executeInternal(JobExecutionContext context) throws JobExecutionException {
        log.info("🚀 开始执行健康基线生成作业");
        long startTime = System.currentTimeMillis();
        
        try {
            // 统计最近7天的数据
            unifiedHealthProcessingService.processUnifiedHealthData("baseline", 7);
            
            long duration = System.currentTimeMillis() - startTime;
            log.info("✅ 健康基线生成作业完成，耗时: {}ms", duration);
            
        } catch (Exception e) {
            log.error("❌ 健康基线生成作业执行失败: {}", e.getMessage(), e);
            throw new JobExecutionException("健康基线生成作业执行失败", e);
        }
    }
}