package com.ljwx.modules.health.job;

import com.ljwx.modules.health.task.HealthBaselineScoreTasks;
import lombok.extern.slf4j.Slf4j;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 组织健康评分生成定时作业 - 集成到mon_scheduler系统
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.job.OrgHealthScoreJob
 * @CreateTime 2025-01-26
 */
@Slf4j
@Component
public class OrgHealthScoreJob implements Job {

    @Autowired
    private HealthBaselineScoreTasks healthBaselineScoreTasks;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        String jobName = context.getJobDetail().getKey().getName();
        log.info("🚀 开始执行组织健康评分生成作业: {}", jobName);
        
        try {
            long startTime = System.currentTimeMillis();
            
            // 调用HealthBaselineScoreTasks中的组织评分生成方法
            healthBaselineScoreTasks.generateOrgHealthScore();
            
            long executionTime = System.currentTimeMillis() - startTime;
            log.info("✅ 组织健康评分生成作业完成: {}, 耗时: {}ms", jobName, executionTime);
            
        } catch (Exception e) {
            log.error("❌ 组织健康评分生成作业失败: {}, 错误: {}", jobName, e.getMessage(), e);
            throw new JobExecutionException("组织健康评分生成失败: " + e.getMessage(), e);
        }
    }
}