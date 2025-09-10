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

package com.ljwx.modules.health.domain.enums;

import com.baomidou.mybatisplus.annotation.EnumValue;
import com.fasterxml.jackson.annotation.JsonValue;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 紧急程度枚举 - V2优化版本
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.enums.UrgencyEnum
 * @CreateTime 2025-09-10 - 15:39:00
 */
@Getter
@AllArgsConstructor
public enum UrgencyEnum {

    /**
     * 低紧急度
     */
    LOW("low", "低", "一般消息", "#52c41a"),

    /**
     * 中等紧急度
     */
    MEDIUM("medium", "中", "普通重要", "#1890ff"),

    /**
     * 高紧急度
     */
    HIGH("high", "高", "重要消息", "#fa8c16"),

    /**
     * 紧急
     */
    CRITICAL("critical", "紧急", "紧急处理", "#ff4d4f");

    /**
     * 数据库存储值
     */
    @EnumValue
    @JsonValue
    private final String code;

    /**
     * 显示名称
     */
    private final String displayName;

    /**
     * 描述信息
     */
    private final String description;

    /**
     * 颜色标识
     */
    private final String color;

    /**
     * 根据代码获取枚举
     */
    public static UrgencyEnum getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (UrgencyEnum urgency : values()) {
            if (urgency.getCode().equals(code)) {
                return urgency;
            }
        }
        return null;
    }

    /**
     * 检查是否为高优先级
     */
    public boolean isHighUrgency() {
        return this == HIGH || this == CRITICAL;
    }

    /**
     * 检查是否需要立即处理
     */
    public boolean requiresImmediateAction() {
        return this == CRITICAL;
    }

    /**
     * 获取紧急度数值 (1-4)
     */
    public int getUrgencyLevel() {
        switch (this) {
            case LOW:
                return 1;
            case MEDIUM:
                return 2;
            case HIGH:
                return 3;
            case CRITICAL:
                return 4;
            default:
                return 2;
        }
    }

    /**
     * 获取超时时间 (分钟)
     */
    public int getTimeoutMinutes() {
        switch (this) {
            case LOW:
                return 24 * 60; // 24小时
            case MEDIUM:
                return 4 * 60;  // 4小时
            case HIGH:
                return 60;      // 1小时
            case CRITICAL:
                return 15;      // 15分钟
            default:
                return 4 * 60;
        }
    }
}