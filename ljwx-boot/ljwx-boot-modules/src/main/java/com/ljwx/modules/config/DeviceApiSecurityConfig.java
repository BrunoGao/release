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

package com.ljwx.modules.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 设备API安全配置
 * 
 * 由于项目使用Sa-Token认证，设备API的免认证配置通过修改 InterceptorConfiguration 实现。
 * 此配置类提供设备API访问日志功能。
 * 
 * 设备端免认证接口：
 * 1. 配置管理接口 - 设备获取配置信息
 * 2. 批量上传接口 - 设备上传健康数据、设备信息、事件数据
 * 3. 健康检查接口 - 服务状态检查
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName DeviceApiSecurityConfig
 * @CreateTime 2024-12-16
 */
@Configuration
public class DeviceApiSecurityConfig {

    /**
     * 设备API访问日志配置
     * 记录设备访问情况，便于监控和调试
     */
    @Bean
    public DeviceApiAccessLogger deviceApiAccessLogger() {
        return new DeviceApiAccessLogger();
    }
}

/**
 * 设备API访问日志记录器
 */
class DeviceApiAccessLogger {
    
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(DeviceApiAccessLogger.class);
    
    /**
     * 记录设备API访问
     */
    public void logDeviceAccess(String deviceId, String endpoint, String clientIP) {
        log.info("📱 设备API访问: deviceId={}, endpoint={}, clientIP={}", deviceId, endpoint, clientIP);
    }
    
    /**
     * 记录设备API错误
     */
    public void logDeviceError(String deviceId, String endpoint, String error) {
        log.warn("❌ 设备API错误: deviceId={}, endpoint={}, error={}", deviceId, endpoint, error);
    }
}