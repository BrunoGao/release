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
import com.ljwx.modules.stream.domain.dto.CommonEventUploadRequest;

import java.util.Map;

/**
 * 通用事件流处理服务接口
 * 
 * 兼容ljwx-bigscreen的通用事件上传接口，用于处理SOS、跌倒检测等紧急事件
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName ICommonEventStreamService
 * @CreateTime 2024-12-16
 */
public interface ICommonEventStreamService {

    /**
     * 上传通用事件
     * 
     * 处理各类通用事件，如SOS紧急求救、跌倒检测、异常行为等
     * 系统会根据事件类型和严重级别触发相应的告警流程
     * 
     * @param request 通用事件上传请求
     * @return 处理结果，包含事件处理状态和告警触发信息
     */
    Result<Map<String, Object>> uploadCommonEvent(CommonEventUploadRequest request);

}