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
import com.ljwx.modules.stream.domain.dto.DeviceMessageSaveRequest;
import com.ljwx.modules.stream.domain.dto.DeviceMessageSendRequest;

import java.util.Map;

/**
 * 设备消息处理服务接口
 * 
 * 兼容ljwx-bigscreen的DeviceMessage相关接口，提供设备消息的保存、发送、接收功能
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName IDeviceMessageService  
 * @CreateTime 2024-12-16
 */
public interface IDeviceMessageService {

    /**
     * 保存设备消息
     * 
     * 将设备消息保存到数据库，支持多种消息类型和优先级设置
     * 
     * @param request 设备消息保存请求
     * @return 保存结果，包含消息ID和保存状态
     */
    Result<Map<String, Object>> saveMessage(DeviceMessageSaveRequest request);

    /**
     * 发送设备消息
     * 
     * 向指定设备或用户发送消息，支持实时推送和离线存储
     * 
     * @param request 设备消息发送请求
     * @return 发送结果，包含发送状态和消息追踪信息
     */
    Result<Map<String, Object>> sendMessage(DeviceMessageSendRequest request);

    /**
     * 接收设备消息
     * 
     * 获取指定设备的消息列表，支持分页和状态过滤
     * 
     * @param deviceSn 设备序列号
     * @return 消息列表，包含消息内容、状态、时间戳等信息
     */
    Result<Map<String, Object>> receiveMessages(String deviceSn);

}