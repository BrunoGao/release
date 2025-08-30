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

package com.ljwx.modules.alert.service;

import com.ljwx.modules.alert.domain.dto.AlertProcessingRequest;
import com.ljwx.modules.alert.domain.dto.AlertProcessingResponse;
import com.ljwx.modules.alert.domain.dto.AnalyzedAlert;
import com.ljwx.modules.alert.domain.dto.PriorityInfo;
import com.ljwx.modules.alert.service.engine.SmartAlertEngine;
import com.ljwx.modules.alert.service.notification.NotificationHub;
import com.ljwx.modules.alert.service.priority.AlertPriorityCalculator;
import com.ljwx.modules.system.service.ISysOrgClosureService;
import com.ljwx.modules.system.domain.dto.OrgHierarchyInfo;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 统一告警系统 - 基于闭包表优化
 * 充分利用已有的组织架构闭包表优化，实现高效的告警分发和处理
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.UnifiedAlertSystem
 * @CreateTime 2024-08-30 - 15:00:00
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UnifiedAlertSystem {

    private final ISysOrgClosureService orgClosureService;
    private final SmartAlertEngine alertEngine;
    private final NotificationHub notificationHub;
    private final AlertPriorityCalculator priorityCalculator;

    /**
     * 统一告警处理流程
     * 
     * @param request 告警处理请求
     * @return 处理结果
     */
    public AlertProcessingResponse processAlert(AlertProcessingRequest request) {
        log.info("开始处理告警: alertType={}, deviceSn={}, customerId={}", 
                request.getAlertType(), request.getDeviceSn(), request.getCustomerId());
        
        long startTime = System.currentTimeMillis();
        
        try {
            // 1. 智能告警分析
            AnalyzedAlert analyzedAlert = alertEngine.analyzeAlert(request);
            log.debug("告警分析完成: alertId={}, confidence={}", 
                    analyzedAlert.getAlertId(), analyzedAlert.getConfidenceScore());
            
            // 2. 基于闭包表的高效组织查询
            List<OrgHierarchyInfo> orgHierarchy = orgClosureService.getNotificationHierarchy(
                    analyzedAlert.getOrgId(), analyzedAlert.getCustomerId()
            );
            log.debug("组织层级查询完成: orgId={}, hierarchySize={}", 
                    analyzedAlert.getOrgId(), orgHierarchy.size());
            
            // 3. 智能优先级计算
            PriorityInfo priorityInfo = priorityCalculator.calculatePriority(
                    analyzedAlert, orgHierarchy
            );
            log.debug("优先级计算完成: priority={}, deadline={}", 
                    priorityInfo.getPriority(), priorityInfo.getProcessingDeadline());
            
            // 4. 统一分发处理
            var distributionResult = notificationHub.distributeAlert(
                    analyzedAlert, orgHierarchy, priorityInfo
            );
            
            long processingTime = System.currentTimeMillis() - startTime;
            log.info("告警处理完成: alertId={}, distributionId={}, processingTime={}ms, recipients={}", 
                    analyzedAlert.getAlertId(), distributionResult.getDistributionId(), 
                    processingTime, distributionResult.getTotalRecipients());
            
            return AlertProcessingResponse.builder()
                    .alertId(analyzedAlert.getAlertId())
                    .success(true)
                    .processingTime(processingTime)
                    .distributionId(distributionResult.getDistributionId())
                    .totalRecipients(distributionResult.getTotalRecipients())
                    .estimatedDeliveryTime(distributionResult.getEstimatedDeliveryTime())
                    .trackingUrl(distributionResult.getTrackingUrl())
                    .confidenceScore(analyzedAlert.getConfidenceScore())
                    .priority(priorityInfo.getPriority())
                    .processedAt(LocalDateTime.now())
                    .build();
            
        } catch (Exception e) {
            long processingTime = System.currentTimeMillis() - startTime;
            log.error("告警处理失败: alertType={}, deviceSn={}, error={}, processingTime={}ms", 
                    request.getAlertType(), request.getDeviceSn(), e.getMessage(), processingTime, e);
            
            return AlertProcessingResponse.builder()
                    .success(false)
                    .processingTime(processingTime)
                    .errorMessage(e.getMessage())
                    .processedAt(LocalDateTime.now())
                    .build();
        }
    }
    
    /**
     * 批量处理告警
     * 
     * @param requests 批量告警请求
     * @return 批量处理结果
     */
    public List<AlertProcessingResponse> processBatchAlerts(List<AlertProcessingRequest> requests) {
        log.info("开始批量处理告警: size={}", requests.size());
        
        long startTime = System.currentTimeMillis();
        
        List<AlertProcessingResponse> responses = requests.parallelStream()
                .map(this::processAlert)
                .toList();
        
        long totalTime = System.currentTimeMillis() - startTime;
        long successCount = responses.stream()
                .mapToLong(r -> r.isSuccess() ? 1 : 0)
                .sum();
        
        log.info("批量告警处理完成: total={}, success={}, failed={}, totalTime={}ms", 
                requests.size(), successCount, requests.size() - successCount, totalTime);
        
        return responses;
    }
}