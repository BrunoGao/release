/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.alert.test;

import com.ljwx.modules.alert.service.UnifiedAlertSystem;
import com.ljwx.modules.alert.domain.dto.AlertProcessingRequest;
import com.ljwx.modules.alert.domain.dto.AlertProcessingResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 告警系统性能测试
 * 用于验证统一告警系统的性能和功能
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.test.AlertSystemPerformanceTest
 * @CreateTime 2024-08-30 - 22:30:00
 */
@Slf4j
@Component
public class AlertSystemPerformanceTest implements CommandLineRunner {

    @Autowired(required = false)
    private UnifiedAlertSystem unifiedAlertSystem;
    
    private final ExecutorService executorService = Executors.newFixedThreadPool(10);

    @Override
    public void run(String... args) throws Exception {
        if (unifiedAlertSystem == null) {
            log.info("告警系统未初始化，跳过性能测试");
            return;
        }
        
        log.info("=== 开始告警系统性能测试 ===");
        
        try {
            // 测试1：单个告警处理
            testSingleAlertProcessing();
            
            // 测试2：批量告警处理
            testBatchAlertProcessing();
            
            // 测试3：并发告警处理
            testConcurrentAlertProcessing();
            
            // 测试4：不同类型告警处理
            testDifferentAlertTypes();
            
            log.info("=== 告警系统性能测试完成 ===");
            
        } catch (Exception e) {
            log.error("性能测试执行失败", e);
        } finally {
            executorService.shutdown();
        }
    }

    /**
     * 测试单个告警处理
     */
    private void testSingleAlertProcessing() {
        log.info("--- 测试1：单个告警处理 ---");
        
        try {
            AlertProcessingRequest request = createTestAlert("HEART_RATE", "HIGH");
            
            long startTime = System.currentTimeMillis();
            AlertProcessingResponse response = unifiedAlertSystem.processAlert(request);
            long processingTime = System.currentTimeMillis() - startTime;
            
            log.info("单个告警处理结果: success={}, alertId={}, time={}ms", 
                    response.isSuccess(), response.getAlertId(), processingTime);
            
            if (response.isSuccess()) {
                log.info("  - 分发ID: {}", response.getDistributionId());
                log.info("  - 接收人数: {}", response.getTotalRecipients());
                log.info("  - 置信度: {:.2%}", response.getConfidenceScore());
                log.info("  - 优先级: {}", response.getPriority());
            }
            
        } catch (Exception e) {
            log.error("单个告警处理测试失败", e);
        }
    }

    /**
     * 测试批量告警处理
     */
    private void testBatchAlertProcessing() {
        log.info("--- 测试2：批量告警处理 ---");
        
        try {
            List<AlertProcessingRequest> requests = Arrays.asList(
                createTestAlert("HEART_RATE", "CRITICAL"),
                createTestAlert("BLOOD_PRESSURE", "HIGH"),
                createTestAlert("DEVICE_OFFLINE", "MEDIUM"),
                createTestAlert("FALL_DETECTION", "HIGH"),
                createTestAlert("SOS", "CRITICAL")
            );
            
            long startTime = System.currentTimeMillis();
            List<AlertProcessingResponse> responses = unifiedAlertSystem.processBatchAlerts(requests);
            long processingTime = System.currentTimeMillis() - startTime;
            
            long successCount = responses.stream().mapToLong(r -> r.isSuccess() ? 1 : 0).sum();
            
            log.info("批量告警处理结果: total={}, success={}, failed={}, time={}ms", 
                    responses.size(), successCount, responses.size() - successCount, processingTime);
            log.info("  - 平均处理时间: {:.1f}ms/alert", (double) processingTime / requests.size());
            
        } catch (Exception e) {
            log.error("批量告警处理测试失败", e);
        }
    }

    /**
     * 测试并发告警处理
     */
    private void testConcurrentAlertProcessing() {
        log.info("--- 测试3：并发告警处理 ---");
        
        try {
            int concurrentCount = 20;
            long startTime = System.currentTimeMillis();
            
            List<CompletableFuture<AlertProcessingResponse>> futures = Arrays.asList(
                new CompletableFuture[concurrentCount]);
            
            for (int i = 0; i < concurrentCount; i++) {
                final int index = i;
                futures.set(i, CompletableFuture.supplyAsync(() -> {
                    try {
                        AlertProcessingRequest request = createTestAlert(
                            "CONCURRENT_TEST_" + index, 
                            index % 2 == 0 ? "HIGH" : "MEDIUM"
                        );
                        return unifiedAlertSystem.processAlert(request);
                    } catch (Exception e) {
                        log.error("并发处理异常: index={}", index, e);
                        return AlertProcessingResponse.builder()
                                .success(false)
                                .errorMessage(e.getMessage())
                                .build();
                    }
                }, executorService));
            }
            
            // 等待所有任务完成
            CompletableFuture<Void> allDone = CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0]));
            allDone.get();
            
            long totalTime = System.currentTimeMillis() - startTime;
            
            // 统计结果
            long successCount = futures.stream()
                    .mapToLong(f -> {
                        try {
                            return f.get().isSuccess() ? 1 : 0;
                        } catch (Exception e) {
                            return 0;
                        }
                    }).sum();
            
            log.info("并发告警处理结果: total={}, success={}, failed={}, totalTime={}ms", 
                    concurrentCount, successCount, concurrentCount - successCount, totalTime);
            log.info("  - 平均处理时间: {:.1f}ms/alert", (double) totalTime / concurrentCount);
            log.info("  - 吞吐量: {:.1f} alerts/second", 1000.0 * concurrentCount / totalTime);
            
        } catch (Exception e) {
            log.error("并发告警处理测试失败", e);
        }
    }

    /**
     * 测试不同类型告警处理
     */
    private void testDifferentAlertTypes() {
        log.info("--- 测试4：不同类型告警处理 ---");
        
        String[] alertTypes = {"HEART_RATE", "BLOOD_PRESSURE", "DEVICE_OFFLINE", "FALL_DETECTION", "SOS"};
        String[] severityLevels = {"CRITICAL", "HIGH", "MEDIUM", "LOW"};
        
        try {
            for (String alertType : alertTypes) {
                for (String severity : severityLevels) {
                    AlertProcessingRequest request = createTestAlert(alertType, severity);
                    
                    long startTime = System.currentTimeMillis();
                    AlertProcessingResponse response = unifiedAlertSystem.processAlert(request);
                    long processingTime = System.currentTimeMillis() - startTime;
                    
                    log.info("告警处理 [{}|{}]: success={}, time={}ms, priority={}", 
                            alertType, severity, response.isSuccess(), processingTime, 
                            response.getPriority());
                }
            }
            
        } catch (Exception e) {
            log.error("不同类型告警处理测试失败", e);
        }
    }

    /**
     * 创建测试告警请求
     */
    private AlertProcessingRequest createTestAlert(String alertType, String severityLevel) {
        return AlertProcessingRequest.builder()
                .alertType(alertType)
                .deviceSn("TEST_DEVICE_" + System.currentTimeMillis() + "_" + Math.random())
                .alertTimestamp(LocalDateTime.now())
                .alertDesc("性能测试告警: " + alertType + " - " + severityLevel)
                .severityLevel(severityLevel)
                .userId(1L)
                .orgId(1L)
                .customerId(1L)
                .ruleId(1L)
                .latitude(new BigDecimal("39.9042"))
                .longitude(new BigDecimal("116.4074"))
                .build();
    }
}