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
import com.ljwx.modules.stream.domain.dto.DeviceInfoUploadRequest;

import java.util.Map;

/**
 * 设备信息流处理服务接口
 * 
 * 兼容ljwx-bigscreen的设备信息上传接口，支持设备注册、状态更新等功能
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName IDeviceInfoStreamService
 * @CreateTime 2024-12-16
 */
public interface IDeviceInfoStreamService {

    /**
     * 上传设备信息
     * 
     * 支持单个和批量设备信息上传，包括设备注册、状态更新、配置同步等
     * 
     * @param request 设备信息上传请求
     * @return 处理结果，包含设备注册/更新状态和设备配置信息
     */
    Result<Map<String, Object>> uploadDeviceInfo(DeviceInfoUploadRequest request);

}