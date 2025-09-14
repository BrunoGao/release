package com.ljwx.modules.health.job;

import com.ljwx.modules.health.service.UnifiedHealthProcessingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.quartz.QuartzJobBean;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 统一健康数据处理任务
 * 按顺序执行：baseline → score → recommendation → cleanup
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-09-13
 */
@Slf4j
@Component
public class UnifiedHealthProcessingJob extends QuartzJobBean {

    @Autowired
    private UnifiedHealthProcessingService unifiedHealthProcessingService;

    @Override
    protected void executeInternal(JobExecutionContext context) throws JobExecutionException {
        log.info("🚀 开始执行统一健康数据处理作业");
        long startTime = System.currentTimeMillis();
        
        try {
            // 统计最近7天的数据
            int days = 7;
            
            // 1. 生成健康基线 (02:00)
            log.info("📊 步骤1: 生成健康基线");
            unifiedHealthProcessingService.processUnifiedHealthData("baseline", days);
            
            // 2. 生成健康评分 (04:00) 
            log.info("📈 步骤2: 生成健康评分");
            unifiedHealthProcessingService.processUnifiedHealthData("score", days);
            
            // 3. 生成健康建议 (需要基于评分结果)
            log.info("💡 步骤3: 生成健康建议");
            unifiedHealthProcessingService.processUnifiedHealthData("recommendation", days);
            
            long duration = System.currentTimeMillis() - startTime;
            log.info("✅ 统一健康数据处理作业完成，总耗时: {}ms", duration);
            
        } catch (Exception e) {
            log.error("❌ 统一健康数据处理作业执行失败: {}", e.getMessage(), e);
            throw new JobExecutionException("统一健康数据处理作业执行失败", e);
        }
    }
}