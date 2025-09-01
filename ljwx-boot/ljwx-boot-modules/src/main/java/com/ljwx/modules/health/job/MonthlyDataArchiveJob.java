package com.ljwx.modules.health.job;

import lombok.extern.slf4j.Slf4j;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import com.ljwx.modules.health.task.HealthBaselineScoreTasks;

/**
 * 月度健康数据归档作业 - 集成到mon_scheduler系统
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.job.MonthlyDataArchiveJob
 * @CreateTime 2025-08-31
 */
@Slf4j
@Component
public class MonthlyDataArchiveJob implements Job {

    @Autowired
    private HealthBaselineScoreTasks healthBaselineScoreTasks;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        String jobName = context.getJobDetail().getKey().getName();
        log.info("🚀 开始执行月度健康数据归档作业: {}", jobName);
        
        try {
            long startTime = System.currentTimeMillis();
            
            // 执行月度数据归档（分表）
            healthBaselineScoreTasks.archiveAndResetUserHealthTable();
            
            long executionTime = System.currentTimeMillis() - startTime;
            log.info("✅ 月度健康数据归档作业完成: {}, 耗时: {}ms", jobName, executionTime);
            
        } catch (Exception e) {
            log.error("❌ 月度健康数据归档作业失败: {}, 错误: {}", jobName, e.getMessage(), e);
            throw new JobExecutionException("月度数据归档失败: " + e.getMessage(), e);
        }
    }
}