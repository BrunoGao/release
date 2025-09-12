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
 * 用户类型枚举
 * 
 * <p>用于优化管理员用户查询性能的冗余字段枚举定义</p>
 * <p>配合 admin_level 字段实现高效的用户类型判断</p>
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.enums.UserType
 * @CreateTime 2025-09-12 - 16:35:30
 */
@Getter
public enum UserType {
    /**
     * 普通用户 - 没有管理权限
     */
    NORMAL(0, "普通用户"),
    
    /**
     * 部门管理员 - 可管理所在部门的用户和资源
     */
    DEPT_ADMIN(1, "部门管理员"),
    
    /**
     * 租户管理员 - 可管理整个租户的用户和资源
     */
    TENANT_ADMIN(2, "租户管理员"),
    
    /**
     * 超级管理员 - 拥有系统最高权限，可管理所有租户和用户
     */
    SUPER_ADMIN(3, "超级管理员");

    private final int code;
    private final String description;

    UserType(int code, String description) {
        this.code = code;
        this.description = description;
    }

    /**
     * 根据代码获取用户类型
     *
     * @param code 用户类型代码
     * @return UserType 用户类型枚举，如果找不到则返回 NORMAL
     */
    public static UserType fromCode(int code) {
        for (UserType userType : values()) {
            if (userType.code == code) {
                return userType;
            }
        }
        return NORMAL; // 默认返回普通用户
    }

    /**
     * 根据代码获取用户类型（可空返回）
     *
     * @param code 用户类型代码
     * @return UserType 用户类型枚举，如果找不到则返回 null
     */
    public static UserType fromCodeNullable(Integer code) {
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
        return this != NORMAL;
    }

    /**
     * 判断是否为部门级管理员
     *
     * @return true 如果是部门管理员，false 其他情况
     */
    public boolean isDeptAdmin() {
        return this == DEPT_ADMIN;
    }

    /**
     * 判断是否为租户级管理员
     *
     * @return true 如果是租户管理员，false 其他情况
     */
    public boolean isTenantAdmin() {
        return this == TENANT_ADMIN;
    }

    /**
     * 判断是否为超级管理员
     *
     * @return true 如果是超级管理员，false 其他情况
     */
    public boolean isSuperAdmin() {
        return this == SUPER_ADMIN;
    }

    /**
     * 判断是否为顶级管理员（租户管理员或超级管理员）
     *
     * @return true 如果是顶级管理员，false 其他情况
     */
    public boolean isTopLevelAdmin() {
        return this == TENANT_ADMIN || this == SUPER_ADMIN;
    }

    /**
     * 比较管理级别高低
     *
     * @param other 另一个用户类型
     * @return 如果当前类型级别更高返回正数，相等返回0，更低返回负数
     */
    public int compareLevel(UserType other) {
        return Integer.compare(this.code, other.code);
    }
}