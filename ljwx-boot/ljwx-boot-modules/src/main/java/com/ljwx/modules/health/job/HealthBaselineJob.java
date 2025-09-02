package com.ljwx.modules.health.job;

import lombok.extern.slf4j.Slf4j;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import com.ljwx.modules.health.task.HealthBaselineScoreTasks;

/**
 * 健康基线生成定时作业 - 集成到mon_scheduler系统
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.job.HealthBaselineJob
 * @CreateTime 2025-08-31
 */
@Slf4j
@Component
public class HealthBaselineJob implements Job {

    @Autowired
    private HealthBaselineScoreTasks healthBaselineScoreTasks;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        String jobName = context.getJobDetail().getKey().getName();
        log.info("🚀 开始执行健康基线生成作业: {}", jobName);
        
        try {
            long startTime = System.currentTimeMillis();
            
            // 执行用户健康基线生成
            healthBaselineScoreTasks.generateUserHealthBaseline();
            
            long executionTime = System.currentTimeMillis() - startTime;
            log.info("✅ 健康基线生成作业完成: {}, 耗时: {}ms", jobName, executionTime);
            
        } catch (Exception e) {
            log.error("❌ 健康基线生成作业失败: {}, 错误: {}", jobName, e.getMessage(), e);
            throw new JobExecutionException("健康基线生成失败: " + e.getMessage(), e);
        }
    }
}