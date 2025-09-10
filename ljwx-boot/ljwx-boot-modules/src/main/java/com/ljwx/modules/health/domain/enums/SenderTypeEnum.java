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
 * 发送者类型枚举 - V2优化版本
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.enums.SenderTypeEnum
 * @CreateTime 2025-09-10 - 15:37:00
 */
@Getter
@AllArgsConstructor
public enum SenderTypeEnum {

    /**
     * 系统发送
     */
    SYSTEM("system", "系统", "自动系统消息"),

    /**
     * 管理员发送
     */
    ADMIN("admin", "管理员", "管理员手动发送"),

    /**
     * 普通用户发送
     */
    USER("user", "用户", "普通用户发送"),

    /**
     * 自动发送 (告警等)
     */
    AUTO("auto", "自动", "规则自动触发");

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
     * 根据代码获取枚举
     */
    public static SenderTypeEnum getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (SenderTypeEnum type : values()) {
            if (type.getCode().equals(code)) {
                return type;
            }
        }
        return null;
    }

    /**
     * 检查是否为系统级发送
     */
    public boolean isSystemLevel() {
        return this == SYSTEM || this == AUTO;
    }

    /**
     * 检查是否为人工发送
     */
    public boolean isManual() {
        return this == ADMIN || this == USER;
    }

    /**
     * 获取权限级别
     */
    public int getAuthorityLevel() {
        switch (this) {
            case SYSTEM:
                return 4;
            case AUTO:
                return 3;
            case ADMIN:
                return 2;
            case USER:
                return 1;
            default:
                return 0;
        }
    }
}