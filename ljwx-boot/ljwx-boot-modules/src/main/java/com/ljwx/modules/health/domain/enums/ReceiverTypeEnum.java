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
 * 接收者类型枚举 - V2优化版本
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.enums.ReceiverTypeEnum
 * @CreateTime 2025-09-10 - 15:38:00
 */
@Getter
@AllArgsConstructor
public enum ReceiverTypeEnum {

    /**
     * 设备接收
     */
    DEVICE("device", "设备", "单个设备"),

    /**
     * 用户接收
     */
    USER("user", "用户", "单个用户"),

    /**
     * 部门接收
     */
    DEPARTMENT("department", "部门", "部门群发"),

    /**
     * 组织接收
     */
    ORGANIZATION("organization", "组织", "组织群发");

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
    public static ReceiverTypeEnum getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (ReceiverTypeEnum type : values()) {
            if (type.getCode().equals(code)) {
                return type;
            }
        }
        return null;
    }

    /**
     * 检查是否为群发类型
     */
    public boolean isGroupType() {
        return this == DEPARTMENT || this == ORGANIZATION;
    }

    /**
     * 检查是否为单发类型
     */
    public boolean isIndividualType() {
        return this == DEVICE || this == USER;
    }

    /**
     * 获取扩散范围级别
     */
    public int getScopeLevel() {
        switch (this) {
            case ORGANIZATION:
                return 4;
            case DEPARTMENT:
                return 3;
            case USER:
                return 2;
            case DEVICE:
                return 1;
            default:
                return 0;
        }
    }
}