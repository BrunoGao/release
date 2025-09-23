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

package com.ljwx.modules.health.domain.dto.alert.rules;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;
import java.math.BigDecimal;

/**
*  编辑更新 DTO 对象
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.alert.domain.dto.alert.rules.TAlertRulesUpdateDTO
* @CreateTime 2025-02-13 - 14:59:34
*/

@Getter
@Setter
@Schema(name = "TAlertRulesUpdateDTO", description = " 编辑更新 DTO 对象")
public class TAlertRulesUpdateDTO implements Serializable {

    @Schema(description = "ID")
    private Long id;

    private String ruleType;

    private String physicalSign;

    private BigDecimal thresholdMin;

    private BigDecimal thresholdMax;

    private Integer trendDuration;

    private String severityLevel;

    private String alertMessage;

    private String notificationType;

    @Schema(description = "客户ID")
    private Long customerId;

    // 新增字段 - 与AddDTO保持一致，支持完整的规则编辑
    @Schema(description = "规则类别")
    private String ruleCategory;  // SINGLE, COMPOSITE, COMPLEX
    
    @Schema(description = "条件表达式")
    private Object conditionExpression;  // JSON类型
    
    @Schema(description = "时间窗口(秒)")
    private Integer timeWindowSeconds;
    
    @Schema(description = "冷却时间(秒)")
    private Integer cooldownSeconds;
    
    @Schema(description = "优先级")
    private Integer priorityLevel;
    
    @Schema(description = "规则标签")
    private Object ruleTags;  // JSON类型
    
    @Schema(description = "生效开始时间")
    private String effectiveTimeStart;
    
    @Schema(description = "生效结束时间")
    private String effectiveTimeEnd;
    
    @Schema(description = "生效日期")
    private String effectiveDays;
    
    @Schema(description = "版本号")
    private Long version;
    
    @Schema(description = "启用的通知渠道")
    private Object enabledChannels;  // JSON类型
    
    @Schema(description = "严重级别(兼容字段)")
    private String level;  // 映射到 severityLevel
    
    @Schema(description = "是否启用")
    private Boolean isEnabled;
    
    @Schema(description = "逻辑操作符")
    private String logicalOperator;
    
    @Schema(description = "条件列表")
    private Object conditions;
    
    @Schema(description = "阈值类型")
    private String thresholdType;

}