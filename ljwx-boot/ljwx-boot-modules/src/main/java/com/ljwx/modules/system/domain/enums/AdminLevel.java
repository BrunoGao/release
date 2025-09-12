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

package com.ljwx.modules.system.domain.enums;

import lombok.Getter;

/**
 * 管理员级别枚举
 * 
 * <p>用于细分管理员的管理范围和权限级别</p>
 * <p>配合 user_type 字段实现精确的权限控制</p>
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.enums.AdminLevel
 * @CreateTime 2025-09-12 - 16:35:30
 */
@Getter
public enum AdminLevel {
    /**
     * 非管理员 - 普通用户，无管理权限
     */
    NONE(0, "非管理员"),
    
    /**
     * 部门级管理员 - 可管理所在部门的用户和资源
     */
    DEPT_LEVEL(1, "部门级管理员"),
    
    /**
     * 租户级管理员 - 可管理整个租户内的所有部门、用户和资源
     */
    TENANT_LEVEL(2, "租户级管理员"),
    
    /**
     * 系统级管理员 - 拥有系统最高权限，可管理所有租户
     */
    SYSTEM_LEVEL(3, "系统级管理员");

    private final int code;
    private final String description;

    AdminLevel(int code, String description) {
        this.code = code;
        this.description = description;
    }

    /**
     * 根据代码获取管理级别
     *
     * @param code 管理级别代码
     * @return AdminLevel 管理级别枚举，如果找不到则返回 NONE
     */
    public static AdminLevel fromCode(int code) {
        for (AdminLevel adminLevel : values()) {
            if (adminLevel.code == code) {
                return adminLevel;
            }
        }
        return NONE; // 默认返回非管理员
    }

    /**
     * 根据代码获取管理级别（可空返回）
     *
     * @param code 管理级别代码
     * @return AdminLevel 管理级别枚举，如果找不到则返回 null
     */
    public static AdminLevel fromCodeNullable(Integer code) {
        if (code == null) {
            return null;
        }
        return fromCode(code);
    }

    /**
     * 判断是否为管理员
     *
     * @return true 如果是管理员，false 如果是普通用户
     */
    public boolean isAdmin() {
        return this != NONE;
    }

    /**
     * 判断是否为部门级管理员
     *
     * @return true 如果是部门级管理员，false 其他情况
     */
    public boolean isDeptLevel() {
        return this == DEPT_LEVEL;
    }

    /**
     * 判断是否为租户级管理员
     *
     * @return true 如果是租户级管理员，false 其他情况
     */
    public boolean isTenantLevel() {
        return this == TENANT_LEVEL;
    }

    /**
     * 判断是否为系统级管理员
     *
     * @return true 如果是系统级管理员，false 其他情况
     */
    public boolean isSystemLevel() {
        return this == SYSTEM_LEVEL;
    }

    /**
     * 判断是否为顶级管理员（租户级或系统级）
     *
     * @return true 如果是顶级管理员，false 其他情况
     */
    public boolean isTopLevel() {
        return this == TENANT_LEVEL || this == SYSTEM_LEVEL;
    }

    /**
     * 判断是否有权限管理指定级别的用户
     *
     * @param targetLevel 目标用户的管理级别
     * @return true 如果有权限管理，false 如果没有权限
     */
    public boolean canManage(AdminLevel targetLevel) {
        return this.code > targetLevel.code;
    }

    /**
     * 比较管理级别高低
     *
     * @param other 另一个管理级别
     * @return 如果当前级别更高返回正数，相等返回0，更低返回负数
     */
    public int compareLevel(AdminLevel other) {
        return Integer.compare(this.code, other.code);
    }

    /**
     * 获取最低要求的管理级别
     *
     * @param level1 级别1
     * @param level2 级别2
     * @return 两个级别中较高的级别
     */
    public static AdminLevel max(AdminLevel level1, AdminLevel level2) {
        return level1.code > level2.code ? level1 : level2;
    }

    /**
     * 获取较低的管理级别
     *
     * @param level1 级别1
     * @param level2 级别2
     * @return 两个级别中较低的级别
     */
    public static AdminLevel min(AdminLevel level1, AdminLevel level2) {
        return level1.code < level2.code ? level1 : level2;
    }
}