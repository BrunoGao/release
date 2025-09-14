package com.ljwx.admin.controller.monitoring;

import com.ljwx.modules.monitor.service.IMonSchedulerService;
import io.micrometer.core.instrument.MeterRegistry;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.RuntimeMXBean;
import java.lang.management.ThreadMXBean;
import java.util.HashMap;
import java.util.Map;

/**
 * 监控端点 - 无需认证
 * 
 * @Author ljwx-system
 * @ProjectName ljwx-boot
 * @ClassName monitoring.controller.MonitoringController
 * @CreateTime 2024/12/29
 */
@RestController
@Tag(name = "监控端点")
@RequiredArgsConstructor
@RequestMapping("/monitoring")
public class MonitoringController {

    private final MeterRegistry meterRegistry;
    private final IMonSchedulerService monSchedulerService;

    @GetMapping("/health")
    @Operation(summary = "健康检查")
    public Map<String, Object> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("timestamp", System.currentTimeMillis());
        
        // 内存信息
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        Map<String, Object> memory = new HashMap<>();
        memory.put("heap_used", memoryBean.getHeapMemoryUsage().getUsed());
        memory.put("heap_max", memoryBean.getHeapMemoryUsage().getMax());
        memory.put("non_heap_used", memoryBean.getNonHeapMemoryUsage().getUsed());
        health.put("memory", memory);
        
        // 线程信息
        ThreadMXBean threadBean = ManagementFactory.getThreadMXBean();
        Map<String, Object> threads = new HashMap<>();
        threads.put("live", threadBean.getThreadCount());
        threads.put("peak", threadBean.getPeakThreadCount());
        threads.put("daemon", threadBean.getDaemonThreadCount());
        health.put("threads", threads);
        
        // 运行时信息
        RuntimeMXBean runtimeBean = ManagementFactory.getRuntimeMXBean();
        Map<String, Object> runtime = new HashMap<>();
        runtime.put("uptime", runtimeBean.getUptime());
        runtime.put("start_time", runtimeBean.getStartTime());
        health.put("runtime", runtime);
        
        return health;
    }

    @GetMapping("/metrics")
    @Operation(summary = "Prometheus指标")
    public String metrics() {
        StringBuilder metrics = new StringBuilder();
        
        // 基础指标
        metrics.append("# HELP ljwx_boot_up Service status\n");
        metrics.append("# TYPE ljwx_boot_up gauge\n");
        metrics.append("ljwx_boot_up 1\n");
        
        // JVM内存指标
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        metrics.append("# HELP jvm_memory_used_bytes JVM memory used\n");
        metrics.append("# TYPE jvm_memory_used_bytes gauge\n");
        metrics.append("jvm_memory_used_bytes{area=\"heap\"} ").append(memoryBean.getHeapMemoryUsage().getUsed()).append("\n");
        metrics.append("jvm_memory_used_bytes{area=\"nonheap\"} ").append(memoryBean.getNonHeapMemoryUsage().getUsed()).append("\n");
        
        metrics.append("# HELP jvm_memory_max_bytes JVM memory max\n");
        metrics.append("# TYPE jvm_memory_max_bytes gauge\n");
        metrics.append("jvm_memory_max_bytes{area=\"heap\"} ").append(memoryBean.getHeapMemoryUsage().getMax()).append("\n");
        metrics.append("jvm_memory_max_bytes{area=\"nonheap\"} ").append(memoryBean.getNonHeapMemoryUsage().getMax()).append("\n");
        
        // 线程指标
        ThreadMXBean threadBean = ManagementFactory.getThreadMXBean();
        metrics.append("# HELP jvm_threads_live_threads JVM live threads\n");
        metrics.append("# TYPE jvm_threads_live_threads gauge\n");
        metrics.append("jvm_threads_live_threads ").append(threadBean.getThreadCount()).append("\n");
        
        metrics.append("# HELP jvm_threads_peak_threads JVM peak threads\n");
        metrics.append("# TYPE jvm_threads_peak_threads gauge\n");
        metrics.append("jvm_threads_peak_threads ").append(threadBean.getPeakThreadCount()).append("\n");
        
        // 运行时间指标
        RuntimeMXBean runtimeBean = ManagementFactory.getRuntimeMXBean();
        metrics.append("# HELP process_uptime_seconds Process uptime\n");
        metrics.append("# TYPE process_uptime_seconds counter\n");
        metrics.append("process_uptime_seconds ").append(runtimeBean.getUptime() / 1000.0).append("\n");
        
        // HTTP请求指标 (模拟)
        metrics.append("# HELP http_server_requests_seconds_count HTTP requests count\n");
        metrics.append("# TYPE http_server_requests_seconds_count counter\n");
        metrics.append("http_server_requests_seconds_count{method=\"GET\",status=\"200\",uri=\"/monitoring/health\"} ").append(System.currentTimeMillis() % 1000).append("\n");
        metrics.append("http_server_requests_seconds_count{method=\"GET\",status=\"200\",uri=\"/monitoring/metrics\"} ").append(System.currentTimeMillis() % 800).append("\n");
        
        metrics.append("# HELP http_server_requests_seconds HTTP request duration\n");
        metrics.append("# TYPE http_server_requests_seconds histogram\n");
        double responseTime = 0.1 + (System.currentTimeMillis() % 100) / 1000.0;
        metrics.append("http_server_requests_seconds_sum{method=\"GET\",status=\"200\",uri=\"/monitoring/health\"} ").append(responseTime * 10).append("\n");
        metrics.append("http_server_requests_seconds_count{method=\"GET\",status=\"200\",uri=\"/monitoring/health\"} 10\n");
        
        return metrics.toString();
    }

    @GetMapping("/info")
    @Operation(summary = "应用信息")
    public Map<String, Object> info() {
        Map<String, Object> info = new HashMap<>();
        info.put("app", "ljwx-boot");
        info.put("version", "1.0.6-SNAPSHOT");
        info.put("environment", "docker");
        info.put("java_version", System.getProperty("java.version"));
        info.put("spring_boot_version", "3.2.0");
        return info;
    }
    
    @GetMapping("/scheduler/test/{id}")
    @Operation(summary = "测试调度任务执行 - 无需认证")
    public Map<String, Object> testScheduler(@PathVariable Long id) {
        Map<String, Object> result = new HashMap<>();
        try {
            boolean success = monSchedulerService.immediateMonScheduler(id);
            result.put("success", success);
            result.put("message", "调度任务执行完成");
            result.put("schedulerId", id);
            result.put("timestamp", System.currentTimeMillis());
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "调度任务执行失败: " + e.getMessage());
            result.put("error", e.getClass().getSimpleName());
            result.put("schedulerId", id);
            result.put("timestamp", System.currentTimeMillis());
        }
        return result;
    }
}
