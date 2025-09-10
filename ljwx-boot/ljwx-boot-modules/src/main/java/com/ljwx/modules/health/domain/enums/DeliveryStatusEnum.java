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
 * 分发状态枚举 - V2优化版本
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.enums.DeliveryStatusEnum
 * @CreateTime 2025-09-10 - 15:46:00
 */
@Getter
@AllArgsConstructor
public enum DeliveryStatusEnum {

    /**
     * 等待分发
     */
    PENDING("pending", "等待分发", "等待发送到目标"),

    /**
     * 已送达
     */
    DELIVERED("delivered", "已送达", "已成功送达目标"),

    /**
     * 已确认
     */
    ACKNOWLEDGED("acknowledged", "已确认", "目标已确认收到"),

    /**
     * 分发失败
     */
    FAILED("failed", "分发失败", "无法送达目标"),

    /**
     * 已过期
     */
    EXPIRED("expired", "已过期", "超过有效期未送达"),

    /**
     * 已取消
     */
    CANCELLED("cancelled", "已取消", "手动取消分发");

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
    public static DeliveryStatusEnum getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (DeliveryStatusEnum status : values()) {
            if (status.getCode().equals(code)) {
                return status;
            }
        }
        return null;
    }

    /**
     * 检查是否为终止状态
     */
    public boolean isFinalStatus() {
        return this == ACKNOWLEDGED || this == FAILED || this == EXPIRED || this == CANCELLED;
    }

    /**
     * 检查是否为成功状态
     */
    public boolean isSuccessStatus() {
        return this == DELIVERED || this == ACKNOWLEDGED;
    }

    /**
     * 检查是否为失败状态
     */
    public boolean isFailureStatus() {
        return this == FAILED || this == EXPIRED || this == CANCELLED;
    }

    /**
     * 检查是否可以重试
     */
    public boolean canRetry() {
        return this == PENDING || this == FAILED;
    }

    /**
     * 获取状态权重 (用于排序显示)
     */
    public int getStatusWeight() {
        switch (this) {
            case FAILED:
                return 6;
            case EXPIRED:
                return 5;
            case CANCELLED:
                return 4;
            case PENDING:
                return 3;
            case DELIVERED:
                return 2;
            case ACKNOWLEDGED:
                return 1;
            default:
                return 0;
        }
    }
}