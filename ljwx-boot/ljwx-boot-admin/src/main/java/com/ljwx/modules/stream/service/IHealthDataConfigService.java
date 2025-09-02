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

package com.ljwx.modules.stream.service;

import com.ljwx.common.api.Result;

import java.util.Map;

/**
 * 健康数据配置服务接口
 * 
 * 兼容ljwx-bigscreen的健康数据配置获取接口，提供设备配置和数据采集参数管理
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName IHealthDataConfigService
 * @CreateTime 2024-12-16
 */
public interface IHealthDataConfigService {

    /**
     * 获取健康数据配置
     * 
     * 根据客户ID和设备序列号获取对应的健康数据采集配置，包括：
     * - 数据采集频率和间隔
     * - 健康指标阈值设置  
     * - 告警规则配置
     * - 设备特定参数
     * 
     * @param customerId 客户ID，可为空则返回默认配置
     * @param deviceSn 设备序列号，可为空则返回通用配置
     * @return 配置数据，包含采集参数、阈值设置、告警配置等
     */
    Result<Map<String, Object>> fetchHealthDataConfig(String customerId, String deviceSn);

}