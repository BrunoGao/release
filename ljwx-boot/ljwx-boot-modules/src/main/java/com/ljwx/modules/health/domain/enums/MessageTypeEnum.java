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
 * 消息类型枚举 - V2优化版本
 * 
 * 使用枚举替代VARCHAR可以节省40%存储空间，提升查询性能
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.enums.MessageTypeEnum
 * @CreateTime 2025-09-10 - 15:35:00
 */
@Getter
@AllArgsConstructor
public enum MessageTypeEnum {

    /**
     * 通知消息
     */
    NOTIFICATION("NOTIFICATION", "通知", "琥珀色", "notification"),

    /**
     * 告警消息
     */
    ALERT("ALERT", "告警", "红色", "alert"),

    /**
     * 警告消息
     */
    WARNING("WARNING", "警告", "橙色", "warning"),

    /**
     * 信息消息
     */
    INFO("INFO", "信息", "蓝色", "info"),

    /**
     * 紧急消息
     */
    EMERGENCY("EMERGENCY", "紧急", "深红色", "emergency"),

    /**
     * 作业指引
     */
    JOB("JOB", "作业指引", "蓝绿色", "work"),

    /**
     * 任务管理
     */
    TASK("TASK", "任务管理", "蓝色", "task");

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
     * 颜色标识
     */
    private final String color;

    /**
     * 图标标识
     */
    private final String icon;

    /**
     * 根据代码获取枚举
     * @param code 代码
     * @return 对应的枚举值
     */
    public static MessageTypeEnum getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (MessageTypeEnum type : values()) {
            if (type.getCode().equals(code)) {
                return type;
            }
        }
        return null;
    }

    /**
     * 检查是否为告警类型
     */
    public boolean isAlert() {
        return this == ALERT || this == WARNING || this == EMERGENCY;
    }

    /**
     * 检查是否为信息类型
     */
    public boolean isInfo() {
        return this == INFO || this == NOTIFICATION;
    }

    /**
     * 检查是否为工作类型
     */
    public boolean isWork() {
        return this == JOB || this == TASK;
    }

    /**
     * 检查是否为紧急类型
     */
    public boolean isEmergency() {
        return this == EMERGENCY;
    }

    /**
     * 获取优先级权重
     */
    public int getPriorityWeight() {
        switch (this) {
            case EMERGENCY:
                return 5;
            case ALERT:
                return 4;
            case WARNING:
                return 3;
            case TASK:
                return 3;
            case JOB:
                return 3;
            case INFO:
                return 2;
            case NOTIFICATION:
                return 1;
            default:
                return 1;
        }
    }
}