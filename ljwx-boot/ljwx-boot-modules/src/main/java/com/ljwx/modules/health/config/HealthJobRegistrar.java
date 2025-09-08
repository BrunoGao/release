package com.ljwx.modules.health.config;

import com.ljwx.modules.health.job.*;
import com.ljwx.modules.monitor.service.IMonSchedulerService;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.quartz.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Component;

/**
 * 健康相关Job自动注册器
 * 系统启动时自动将健康相关的Job类注册到Quartz调度器中
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.config.HealthJobRegistrar
 * @CreateTime 2025-09-08
 */
@Slf4j
@Component
public class HealthJobRegistrar {

    @Autowired
    @Qualifier("schedulerBean")
    private Scheduler scheduler;

    @Autowired
    private ApplicationContext applicationContext;

    @Autowired
    private IMonSchedulerService monSchedulerService;

    // 健康相关的Job类映射
    private static final Class<? extends Job>[] HEALTH_JOB_CLASSES = new Class[]{
            WeightValidationJob.class,
            HealthBaselineJob.class,
            DepartmentHealthAggregationJob.class,
            OrgHealthBaselineJob.class,
            DepartmentHealthScoreJob.class,
            HealthRecommendationJob.class,
            HealthScoreJob.class,
            OrgHealthScoreJob.class,
            HealthDataCleanupJob.class,
            MonthlyDataArchiveJob.class
    };

    @PostConstruct
    public void registerHealthJobs() {
        log.info("🚀 开始注册健康相关Job类到Quartz调度器...");
        
        try {
            int registeredCount = 0;
            
            for (Class<? extends Job> jobClass : HEALTH_JOB_CLASSES) {
                try {
                    registerJobClass(jobClass);
                    registeredCount++;
                } catch (Exception e) {
                    log.warn("⚠️ 注册Job类失败: {}, 错误: {}", jobClass.getSimpleName(), e.getMessage());
                }
            }
            
            log.info("✅ 健康Job类注册完成，成功注册: {}/{} 个", registeredCount, HEALTH_JOB_CLASSES.length);
            
            // 注册额外的Job映射（在基础Job注册完成后）
            registerAdditionalJobMappings();
            
            // 同步数据库中的调度任务到Quartz
            syncDatabaseJobsToQuartz();
            
        } catch (Exception e) {
            log.error("❌ 健康Job注册过程失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 注册单个Job类
     */
    private void registerJobClass(Class<? extends Job> jobClass) throws Exception {
        String jobName = getJobNameFromClass(jobClass);
        String jobGroup = "HealthGroup";
        
        // 检查Job是否已存在
        JobKey jobKey = JobKey.jobKey(jobName, jobGroup);
        if (scheduler.checkExists(jobKey)) {
            log.debug("🔍 Job已存在，跳过: {}.{}", jobGroup, jobName);
            return;
        }
        
        // 创建JobDetail，但不添加Trigger（由数据库配置管理）
        JobDetail jobDetail = JobBuilder.newJob(jobClass)
                .withIdentity(jobName, jobGroup)
                .withDescription("健康相关定时任务: " + jobClass.getSimpleName())
                .storeDurably(true) // 允许没有trigger的情况下存储
                .build();
        
        // 添加Job到调度器
        scheduler.addJob(jobDetail, false);
        log.debug("✅ 已注册Job: {}.{}", jobGroup, jobName);
    }

    /**
     * 从Job类名推断任务名称
     */
    private String getJobNameFromClass(Class<? extends Job> jobClass) {
        String className = jobClass.getSimpleName();
        
        // 根据类名映射到数据库中的job_name
        return switch (className) {
            case "WeightValidationJob" -> "WeightConfigValidation";
            case "HealthBaselineJob" -> "UserHealthBaseline";
            case "DepartmentHealthAggregationJob" -> "DepartmentHealthBaseline";
            case "OrgHealthBaselineJob" -> "OrgHealthBaseline";
            case "DepartmentHealthScoreJob" -> "DepartmentHealthScore";
            case "HealthRecommendationJob" -> "HealthRecommendation";
            case "HealthScoreJob" -> "UserHealthScore";
            case "OrgHealthScoreJob" -> "OrgHealthScore";
            case "HealthDataCleanupJob" -> "HealthDataCleanup";
            case "MonthlyDataArchiveJob" -> "MonthlyDataArchive";
            default -> className.replace("Job", "");
        };
    }

    /**
     * 注册额外的Job映射（一个Job类对应多个数据库任务名）
     */
    private void registerAdditionalJobMappings() {
        log.info("🔄 注册额外的Job映射...");
        
        try {
            // MonthlyDataArchiveJob 同时对应 HealthTableArchive 任务
            String jobGroup = "HealthGroup";
            JobKey sourceJobKey = JobKey.jobKey("MonthlyDataArchive", jobGroup);
            JobKey targetJobKey = JobKey.jobKey("HealthTableArchive", jobGroup);
            
            if (scheduler.checkExists(sourceJobKey) && !scheduler.checkExists(targetJobKey)) {
                // 复制JobDetail给HealthTableArchive使用
                JobDetail sourceJob = scheduler.getJobDetail(sourceJobKey);
                JobDetail targetJob = JobBuilder.newJob(MonthlyDataArchiveJob.class)
                        .withIdentity(targetJobKey)
                        .withDescription("健康数据按月分表任务 (映射到MonthlyDataArchiveJob)")
                        .storeDurably(true)
                        .build();
                        
                scheduler.addJob(targetJob, false);
                log.info("✅ 已创建Job映射: {} -> {}", "HealthTableArchive", "MonthlyDataArchiveJob");
            }
            
        } catch (Exception e) {
            log.error("❌ 注册额外Job映射失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 同步数据库中的调度任务配置到Quartz调度器
     */
    private void syncDatabaseJobsToQuartz() {
        log.info("🔄 开始同步数据库调度任务配置到Quartz...");
        
        try {
            // 这里可以调用MonSchedulerService来同步数据库配置
            // 由于具体的同步逻辑可能比较复杂，这里先记录日志
            log.info("📋 数据库调度任务同步功能预留，需要根据具体业务逻辑实现");
            
        } catch (Exception e) {
            log.error("❌ 同步数据库调度任务失败: {}", e.getMessage(), e);
        }
    }
}