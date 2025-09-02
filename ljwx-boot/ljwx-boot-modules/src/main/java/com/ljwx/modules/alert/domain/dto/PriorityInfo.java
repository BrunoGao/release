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

package com.ljwx.modules.alert.domain.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 告警优先级信息DTO
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.domain.dto.PriorityInfo
 * @CreateTime 2024-08-30 - 15:25:00
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PriorityInfo {

    private Integer priority;
    private LocalDateTime processingDeadline;
    private List<EscalationStep> escalationChain;
    private Map<String, Double> calculationBreakdown;
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class EscalationStep {
        private Integer level;
        private Long orgId;
        private String orgName;
        private List<Long> managerIds;
        private long delayMinutes;
    }
}