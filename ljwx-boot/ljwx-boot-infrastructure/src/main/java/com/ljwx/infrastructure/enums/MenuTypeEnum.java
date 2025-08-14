package com.ljwx.infrastructure.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.io.Serializable;

/**
 * 菜单类型枚举类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName enums.com.ljwx.infrastructure.MenuTypeEnum
 * @CreateTime 2024/4/17 - 14:01
 */

@Getter
@AllArgsConstructor
public enum MenuTypeEnum implements Serializable {

    DIRECTORY("1", "目录"),
    MENU("2", "菜单");

    private final String value;

    private final String name;
}
