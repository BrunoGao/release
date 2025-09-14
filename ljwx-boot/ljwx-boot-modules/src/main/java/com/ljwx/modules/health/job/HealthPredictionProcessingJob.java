package com.ljwx.modules.health.job;

import com.ljwx.modules.health.service.UnifiedHealthProcessingService;
import lombok.extern.slf4j.Slf4j;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 健康预测生成任务
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-09-13
 */
@Slf4j
@Component
public class HealthPredictionProcessingJob implements Job {

    @Autowired
    private UnifiedHealthProcessingService unifiedHealthProcessingService;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        log.info("🚀 开始执行健康预测生成作业");
        long startTime = System.currentTimeMillis();
        
        try {
            // 基于最近30天的数据进行预测
            unifiedHealthProcessingService.processUnifiedHealthData("prediction", 30);
            
            long duration = System.currentTimeMillis() - startTime;
            log.info("✅ 健康预测生成作业完成，耗时: {}ms", duration);
            
        } catch (Exception e) {
            log.error("❌ 健康预测生成作业执行失败: {}", e.getMessage(), e);
            throw new JobExecutionException("健康预测生成作业执行失败", e);
        }
    }
}