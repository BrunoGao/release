package com.ljwx.config;

import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.aop.interceptor.SimpleAsyncUncaughtExceptionHandler;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    
    @Override
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(25);
        executor.setThreadNamePrefix("OrgUnits-Async-");
        executor.initialize();
        return executor;
    }
    
    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return new SimpleAsyncUncaughtExceptionHandler();
    }
    
    /**
     * 健康数据查询专用线程池
     * 用于HealthAnalyticsAggregationService的异步并行处理
     */
    @Bean("healthDataQueryExecutor")
    public ThreadPoolExecutor healthDataQueryExecutor() {
        return new ThreadPoolExecutor(
            4,  // 核心线程数
            8,  // 最大线程数
            60L, // 空闲线程存活时间
            TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(50), // 任务队列容量
            r -> {
                Thread thread = new Thread(r, "health-analytics-" + System.currentTimeMillis());
                thread.setDaemon(false); // 非守护线程
                return thread;
            },
            new ThreadPoolExecutor.CallerRunsPolicy() // 拒绝策略
        );
    }
} 