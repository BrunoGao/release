package com.ljwx.modules.health.job;

import com.ljwx.modules.health.service.UnifiedHealthProcessingService;
import lombok.extern.slf4j.Slf4j;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * 部门健康数据聚合作业 - 使用统一处理服务
 * 重构为使用UnifiedHealthProcessingService，统一处理所有健康数据
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.job.DepartmentHealthAggregationJob
 * @CreateTime 2025-09-12
 */
@Slf4j
@Component
public class DepartmentHealthAggregationJob implements Job {

    @Autowired
    private UnifiedHealthProcessingService unifiedHealthProcessingService;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        String jobName = context.getJobDetail().getKey().getName();
        log.info("🏢 开始执行部门健康数据聚合作业: {}", jobName);
        
        try {
            long startTime = System.currentTimeMillis();
            
            // 使用统一处理服务生成基线数据（包含部门和组织级别的聚合）
            unifiedHealthProcessingService.processUnifiedHealthData("baseline", 30);
            
            long executionTime = System.currentTimeMillis() - startTime;
            log.info("✅ 部门健康数据聚合作业完成: {}, 耗时: {}ms", jobName, executionTime);
            
        } catch (Exception e) {
            log.error("❌ 部门健康数据聚合作业失败: {}, 错误: {}", jobName, e.getMessage(), e);
            throw new JobExecutionException("部门健康数据聚合作业执行失败: " + e.getMessage(), e);
        }
    }

    /**
     * 生成部门健康基线（委托给统一处理服务）
     */
    @Transactional(rollbackFor = Exception.class)
    public void generateDepartmentHealthBaselines() {
        log.info("📊 开始生成部门健康基线");
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData("baseline", 30);
            log.info("✅ 部门健康基线生成完成");
        } catch (Exception e) {
            log.error("❌ 部门健康基线生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("部门健康基线生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 生成部门健康评分（委托给统一处理服务）
     */
    @Transactional(rollbackFor = Exception.class)
    public void generateDepartmentHealthScores() {
        log.info("📈 开始生成部门健康评分");
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData("score", 7);
            log.info("✅ 部门健康评分生成完成");
        } catch (Exception e) {
            log.error("❌ 部门健康评分生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("部门健康评分生成失败: " + e.getMessage(), e);
        }
    }
}