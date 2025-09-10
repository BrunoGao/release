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
 * 分发渠道枚举 - V2优化版本
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.enums.ChannelEnum
 * @CreateTime 2025-09-10 - 15:47:00
 */
@Getter
@AllArgsConstructor
public enum ChannelEnum {

    /**
     * 应用内消息
     */
    MESSAGE("message", "应用消息", "应用内消息通知"),

    /**
     * 推送通知
     */
    PUSH("push", "推送通知", "系统推送通知"),

    /**
     * 微信消息
     */
    WECHAT("wechat", "微信消息", "微信企业号消息"),

    /**
     * 手表通知
     */
    WATCH("watch", "手表通知", "智能手表消息"),

    /**
     * 短信通知
     */
    SMS("sms", "短信通知", "手机短信"),

    /**
     * 邮件通知
     */
    EMAIL("email", "邮件通知", "电子邮件");

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
    public static ChannelEnum getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (ChannelEnum channel : values()) {
            if (channel.getCode().equals(code)) {
                return channel;
            }
        }
        return null;
    }

    /**
     * 检查是否为实时渠道
     */
    public boolean isRealTime() {
        return this == PUSH || this == WATCH || this == MESSAGE;
    }

    /**
     * 检查是否为异步渠道
     */
    public boolean isAsync() {
        return this == EMAIL || this == SMS;
    }

    /**
     * 检查是否为第三方渠道
     */
    public boolean isThirdParty() {
        return this == WECHAT || this == EMAIL || this == SMS;
    }

    /**
     * 获取优先级 (越高越优先)
     */
    public int getPriority() {
        switch (this) {
            case WATCH:
                return 6;  // 手表最直接
            case PUSH:
                return 5;  // 推送及时
            case MESSAGE:
                return 4;  // 应用内消息
            case WECHAT:
                return 3;  // 微信消息
            case SMS:
                return 2;  // 短信备用
            case EMAIL:
                return 1;  // 邮件最慢
            default:
                return 0;
        }
    }

    /**
     * 获取预估送达时间 (秒)
     */
    public int getEstimatedDeliveryTime() {
        switch (this) {
            case MESSAGE:
            case WATCH:
                return 1;    // 1秒内
            case PUSH:
                return 5;    // 5秒内
            case WECHAT:
                return 10;   // 10秒内
            case SMS:
                return 30;   // 30秒内
            case EMAIL:
                return 60;   // 1分钟内
            default:
                return 30;
        }
    }
}