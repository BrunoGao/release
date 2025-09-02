package com.ljwx.modules.health.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;

/**
 * 健康任务配置类
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.config.HealthTaskConfiguration
 * @CreateTime 2025-01-26
 */
@Slf4j
@Configuration
@EnableScheduling
public class HealthTaskConfiguration {

    /**
     * 健康任务专用线程池
     */
    @Bean("healthTaskScheduler")
    public TaskScheduler healthTaskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(8); // 线程池大小
        scheduler.setThreadNamePrefix("health-task-");
        scheduler.setAwaitTerminationSeconds(30);
        scheduler.setWaitForTasksToCompleteOnShutdown(true);
        scheduler.setRejectedExecutionHandler((r, executor) -> {
            log.warn("健康任务被拒绝执行: {}", r.toString());
        });
        scheduler.initialize();
        
        log.info("✅ 健康任务调度器已初始化，线程池大小: {}", scheduler.getPoolSize());
        return scheduler;
    }
} 