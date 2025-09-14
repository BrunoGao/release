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

package com.ljwx.modules.health.domain.vo;

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
*  VO 展示类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.alert.domain.vo.TAlertRulesVO
* @CreateTime 2025-02-13 - 14:59:34
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "TAlertRulesVO", description = " VO 对象")
public class TAlertRulesVO extends BaseVO {

    private String ruleType;

    private String physicalSign;

    private BigDecimal thresholdMin;

    private BigDecimal thresholdMax;

    private BigDecimal deviationPercentage;

    private Integer trendDuration;

    private Object parameters;

    private String triggerCondition;

    private String alertMessage;

    private String severityLevel;

    private String notificationType;

    private Long customerId;
    
    // 新增字段
    private String ruleCategory;
    
    private Object conditionExpression;
    
    private Integer timeWindowSeconds;
    
    private Integer cooldownSeconds;
    
    private Integer priorityLevel;
    
    private Object ruleTags;
    
    private String effectiveTimeStart;
    
    private String effectiveTimeEnd;
    
    private String effectiveDays;
    
    private Long version;
    
    private Object enabledChannels;
    
    private String level;
    
    private Boolean isEnabled;

    private String createUser;

    private LocalDateTime createTime;

}