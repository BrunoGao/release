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

package com.ljwx.common.context;

import lombok.extern.slf4j.Slf4j;

/**
 * 用户上下文工具类
 * 用于获取当前登录用户的信息
 * 
 * 注意：这是一个临时实现，用于解决编译问题
 * 实际项目中应该根据具体的认证框架来实现
 *
 * @author bruno.gao
 * @since 2024-01-27
 */
@Slf4j
public class UserContext {

    // 线程本地存储，用于存储当前线程的用户信息
    private static final ThreadLocal<Long> CURRENT_USER_ID = new ThreadLocal<>();
    private static final ThreadLocal<String> CURRENT_USER_NAME = new ThreadLocal<>();
    private static final ThreadLocal<Long> CURRENT_CUSTOMER_ID = new ThreadLocal<>();

    /**
     * 获取当前登录用户ID
     *
     * @return 用户ID
     */
    public static Long getCurrentUserId() {
        Long userId = CURRENT_USER_ID.get();
        if (userId != null) {
            return userId;
        }
        // 返回默认值，避免null异常
        log.debug("当前线程未设置用户ID，返回默认值");
        return 1L; // 默认用户ID
    }

    /**
     * 获取当前登录用户名
     *
     * @return 用户名
     */
    public static String getCurrentUserName() {
        String userName = CURRENT_USER_NAME.get();
        if (userName != null) {
            return userName;
        }
        // 返回默认值，避免null异常
        log.debug("当前线程未设置用户名，返回默认值");
        return "System"; // 默认用户名
    }

    /**
     * 获取当前客户ID（租户ID）
     *
     * @return 客户ID
     */
    public static Long getCustomerId() {
        Long customerId = CURRENT_CUSTOMER_ID.get();
        if (customerId != null) {
            return customerId;
        }
        // 返回默认值，避免null异常
        log.debug("当前线程未设置客户ID，返回默认值");
        return 1L; // 默认客户ID
    }

    /**
     * 设置当前用户ID
     *
     * @param userId 用户ID
     */
    public static void setCurrentUserId(Long userId) {
        CURRENT_USER_ID.set(userId);
    }

    /**
     * 设置用户名
     *
     * @param userName 用户名
     */
    public static void setCurrentUserName(String userName) {
        CURRENT_USER_NAME.set(userName);
    }

    /**
     * 设置客户ID
     *
     * @param customerId 客户ID
     */
    public static void setCustomerId(Long customerId) {
        CURRENT_CUSTOMER_ID.set(customerId);
    }

    /**
     * 检查当前用户是否已登录
     * 
     * 注意：这是一个简化实现，总是返回true
     *
     * @return 是否已登录
     */
    public static boolean isLogin() {
        return true; // 简化实现，总是返回已登录状态
    }

    /**
     * 清空当前线程的用户信息
     */
    public static void clear() {
        CURRENT_USER_ID.remove();
        CURRENT_USER_NAME.remove();
        CURRENT_CUSTOMER_ID.remove();
    }
}