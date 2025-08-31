package com.ljwx.modules.message.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 消息发送范围类型枚举
 * 
 * @author ljwx-system
 * @since 2025-08-31
 */
@Getter
@AllArgsConstructor
public enum MessageScope {
    
    INDIVIDUAL("individual", "个人消息", "发送给特定用户的个人消息"),
    GROUP("group", "群发消息", "发送给特定用户组的消息"),
    DEPARTMENT("department", "部门消息", "发送给整个部门的消息"),
    ORGANIZATION("organization", "组织消息", "发送给整个组织的消息"),
    BROADCAST("broadcast", "全网广播", "广播给所有用户的消息");
    
    private final String code;
    private final String name;
    private final String description;
    
    /**
     * 根据代码获取枚举
     */
    public static MessageScope fromCode(String code) {
        for (MessageScope scope : values()) {
            if (scope.getCode().equals(code)) {
                return scope;
            }
        }
        throw new IllegalArgumentException("未知的消息范围类型: " + code);
    }
    
    /**
     * 是否为群发类型
     */
    public boolean isGroupMessage() {
        return this == GROUP || this == DEPARTMENT || this == ORGANIZATION || this == BROADCAST;
    }
    
    /**
     * 是否需要组织权限验证
     */
    public boolean requiresOrgPermission() {
        return this == DEPARTMENT || this == ORGANIZATION || this == BROADCAST;
    }
}