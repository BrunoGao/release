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

package com.ljwx.modules.config.service;

import com.ljwx.modules.customer.service.ITCustomerConfigService;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import com.ljwx.modules.customer.service.ITInterfaceService;
import com.ljwx.modules.health.service.ITDeviceUserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

/**
 * 统一配置服务
 * 迁移自 Python fetchConfig.py，专门处理多表关联的配置查询
 * 
 * 核心功能：
 * - fetchHealthDataConfig - 获取健康数据配置（多表关联，与Python完全兼容）
 * 
 * 注意：
 * - 配置复制功能由 OrgUnitsChangeListener 自动处理，无需重复实现
 * - 与现有 HealthDataConfigQueryService 配合使用（单表查询）
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName UnifiedConfigService
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
public class UnifiedConfigService {
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    /**
     * 获取健康数据配置 (迁移自 Python fetchConfig.py:fetch_health_data_config)
     * 完全兼容Python接口格式和数据结构
     * 
     * @param customerId 客户ID（可选）
     * @param deviceSn 设备序列号（可选）
     * @return 配置数据（与Python格式完全一致）
     */
    public Map<String, Object> fetchHealthDataConfig(String customerId, String deviceSn) {
        try {
            log.info("🔍 获取健康数据配置: customerId={}, deviceSn={}", customerId, deviceSn);
            
            String resolvedCustomerId;
            String orgId = null;
            String userId = null;
            
            // 1. 根据deviceSn查询sys_user表，检查设备是否绑定员工
            if (deviceSn != null && !deviceSn.trim().isEmpty()) {
                Map<String, Object> deviceInfo = getDeviceUserInfo(deviceSn);
                
                if (deviceInfo != null) {
                    // 设备已绑定员工，使用员工对应的配置
                    resolvedCustomerId = String.valueOf(deviceInfo.get("customer_id"));
                    orgId = String.valueOf(deviceInfo.get("org_id"));
                    userId = String.valueOf(deviceInfo.get("user_id"));
                    log.info("设备已绑定员工: deviceSn={}, customerId={}, userId={}, orgId={}", 
                        deviceSn, resolvedCustomerId, userId, orgId);
                } else {
                    // 设备未绑定员工，使用默认配置
                    resolvedCustomerId = "0";
                    log.info("设备未绑定员工: deviceSn={}, 使用默认配置", deviceSn);
                }
            } else {
                // 没有deviceSn，使用传入的customerId或默认配置
                resolvedCustomerId = customerId != null ? customerId : "0";
                log.info("无设备序列号，使用customerId={}", resolvedCustomerId);
            }
            
            // 2. 查询配置数据 (复用Python的SQL逻辑)
            List<Map<String, Object>> configResults = queryHealthDataConfigJoin(resolvedCustomerId);
            
            if (configResults.isEmpty()) {
                log.warn("未找到customerId={}的配置数据", resolvedCustomerId);
                return createErrorResponse("No configuration found for customerId: " + resolvedCustomerId);
            }
            
            // 3. 格式化返回结果 (保持与Python一致的数据结构)
            Map<String, Object> result = formatHealthDataConfig(configResults, resolvedCustomerId, orgId, userId);
            
            log.info("✅ 健康数据配置获取成功: customerId={}, 配置项数量={}", resolvedCustomerId, configResults.size());
            return result;
            
        } catch (Exception e) {
            log.error("❌ 获取健康数据配置失败: customerId={}, deviceSn={}", customerId, deviceSn, e);
            return createErrorResponse("获取配置失败: " + e.getMessage());
        }
    }
    
    
    
    /**
     * 获取设备用户信息 (调用现有服务)
     */
    private Map<String, Object> getDeviceUserInfo(String deviceSn) {
        if (deviceSn == null || deviceSn.trim().isEmpty()) {
            return null;
        }
        
        try {
            // 从sys_user表查询设备绑定的用户信息（未删除的记录）
            String sql = """
                SELECT u.customer_id, u.id as user_id, u.org_id
                FROM sys_user u
                WHERE u.device_sn = ? AND u.is_deleted = 0
                """;
            
            List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, deviceSn);
            return results.isEmpty() ? null : results.get(0);
        } catch (Exception e) {
            log.warn("获取设备用户信息失败: deviceSn={}", deviceSn, e);
            return null;
        }
    }
    
    /**
     * 查询配置关联数据 (复用Python的SQL逻辑)
     * 完全保持与Python相同的SQL查询
     */
    private List<Map<String, Object>> queryHealthDataConfigJoin(String customerId) {
        String sql = """
            SELECT
                h.data_type,
                h.frequency_interval,
                h.is_enabled,
                h.is_realtime,
                h.warning_high,
                h.warning_low,
                h.warning_cnt,
                c.customer_name,
                c.upload_method,
                c.is_support_license,
                c.license_key,
                c.enable_resume,
                c.upload_retry_count,
                c.cache_max_count,
                c.upload_retry_interval,
                i.name               AS interface_name,
                i.url                AS interface_url,
                i.call_interval      AS interface_call_interval,
                i.is_enabled         AS interface_is_enabled,
                i.api_id             AS interface_api_id,
                i.api_auth           AS interface_api_auth
            FROM t_health_data_config h
            JOIN t_customer_config   c ON h.customer_id = c.customer_id
            JOIN t_interface         i ON h.customer_id = i.customer_id
            WHERE h.customer_id = ?
            """;
        
        return jdbcTemplate.queryForList(sql, customerId);
    }
    
    /**
     * 格式化配置数据 (保持与Python完全一致的格式)
     */
    private Map<String, Object> formatHealthDataConfig(
            List<Map<String, Object>> results, 
            String customerId, 
            String orgId, 
            String userId) {
        
        if (results.isEmpty()) {
            return createErrorResponse("No configuration found");
        }
        
        Map<String, Object> first = results.get(0);
        
        // 构建健康数据配置 (完全复用Python的格式逻辑)
        Map<String, String> healthData = new LinkedHashMap<>();
        for (Map<String, Object> result : results) {
            String dataType = (String) result.get("data_type");
            String value = String.format("%s:%s:%s:%s:%s:%s",
                result.get("frequency_interval"),
                result.get("is_enabled"),
                result.get("is_realtime"),
                result.get("warning_high") != null ? result.get("warning_high") : -1,
                result.get("warning_low") != null ? result.get("warning_low") : -1,
                result.get("warning_cnt") != null ? result.get("warning_cnt") : -1
            );
            healthData.put(dataType, value);
        }
        
        // 构建接口数据配置 (完全复用Python的格式逻辑)
        Map<String, String> interfaceData = new LinkedHashMap<>();
        Set<String> processedInterfaces = new HashSet<>();
        for (Map<String, Object> result : results) {
            String interfaceName = (String) result.get("interface_name");
            if (interfaceName != null && !processedInterfaces.contains(interfaceName)) {
                String value = String.format("%s;%s;%s;%s;%s",
                    result.get("interface_url"),
                    result.get("interface_call_interval"),
                    result.get("interface_is_enabled"),
                    result.get("interface_api_id") != null ? result.get("interface_api_id") : "",
                    result.get("interface_api_auth") != null ? result.get("interface_api_auth") : ""
                );
                interfaceData.put(interfaceName, value);
                processedInterfaces.add(interfaceName);
            }
        }
        
        // 返回与Python完全相同的数据结构
        Map<String, Object> config = new LinkedHashMap<>();
        config.put("customer_name", first.get("customer_name"));
        config.put("customer_id", customerId);
        config.put("org_id", orgId);
        config.put("user_id", userId);
        config.put("upload_method", first.get("upload_method") != null ? first.get("upload_method") : "wifi");
        config.put("enable_resume", first.get("enable_resume") != null ? first.get("enable_resume") : false);
        config.put("upload_retry_count", first.get("upload_retry_count") != null ? first.get("upload_retry_count") : 3);
        config.put("cache_max_count", first.get("cache_max_count") != null ? first.get("cache_max_count") : 100);
        config.put("upload_retry_interval", first.get("upload_retry_interval") != null ? first.get("upload_retry_interval") : 5);
        config.put("health_data", healthData);
        config.put("is_support_license", first.get("is_support_license") != null ? first.get("is_support_license") : false);
        config.put("license_key", first.get("license_key"));
        config.put("interface_data", interfaceData);
        
        return config;
    }
    
    /**
     * 创建错误响应
     */
    private Map<String, Object> createErrorResponse(String error) {
        return Map.of("success", false, "error", error);
    }
    
}