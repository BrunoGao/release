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
import com.ljwx.modules.stream.domain.dto.HealthDataUploadRequest;

import java.util.Map;

/**
 * 健康数据流处理服务接口
 * 
 * 兼容ljwx-bigscreen的健康数据上传接口，提供高性能的批量健康数据处理能力
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName IHealthDataStreamService
 * @CreateTime 2024-12-16
 */
public interface IHealthDataStreamService {

    /**
     * 上传健康数据
     * 
     * 支持单条和批量健康数据上传，完全兼容ljwx-bigscreen的数据格式
     * 
     * @param request 健康数据上传请求
     * @param deviceSn 设备序列号（请求头）
     * @param customerId 客户ID（请求头）
     * @return 处理结果，包含成功/失败状态和统计信息
     */
    Result<Map<String, Object>> uploadHealthData(HealthDataUploadRequest request, String deviceSn, String customerId);

}