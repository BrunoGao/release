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

package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;

/**
*  Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.alert.domain.entity.TAlertRules
* @CreateTime 2025-02-13 - 14:59:34
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_alert_rules")
public class TAlertRules extends BaseEntity {

    private String ruleType;

    private String physicalSign;

    private BigDecimal thresholdMin;

    private BigDecimal thresholdMax;

    private BigDecimal deviationPercentage;

    private Integer trendDuration;

    private String parameters;

    private String triggerCondition;

    private String alertMessage;

    private String severityLevel;

    private String notificationType;

    private Long customerId;
    
    // 新增字段 - 根据数据库迁移脚本
    private String ruleCategory;  // SINGLE, COMPOSITE, COMPLEX
    
    private Object conditionExpression;  // JSON类型
    
    private Integer timeWindowSeconds;
    
    private Integer cooldownSeconds;
    
    private Integer priorityLevel;
    
    private Object ruleTags;  // JSON类型
    
    private java.sql.Time effectiveTimeStart;
    
    private java.sql.Time effectiveTimeEnd;
    
    private String effectiveDays;
    
    private Long version;
    
    private Object enabledChannels;  // JSON类型
    
    // 兼容字段名
    private String level;  // 映射到 severityLevel
    
    private Boolean isEnabled;  // 是否启用

}