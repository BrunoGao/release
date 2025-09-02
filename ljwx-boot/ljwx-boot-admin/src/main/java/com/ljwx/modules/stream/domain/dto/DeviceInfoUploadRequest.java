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

package com.ljwx.modules.stream.domain.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 设备信息上传请求DTO
 * 
 * 兼容ljwx-bigscreen的设备信息格式，支持设备注册、状态更新和配置同步
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName DeviceInfoUploadRequest
 * @CreateTime 2024-12-16
 */
@Data
@Schema(description = "设备信息上传请求")
public class DeviceInfoUploadRequest {

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "设备名称")
    private String deviceName;

    @Schema(description = "设备类型")
    private String deviceType;

    @Schema(description = "设备型号")
    private String deviceModel;

    @Schema(description = "制造商")
    private String manufacturer;

    @Schema(description = "固件版本")
    private String firmwareVersion;

    @Schema(description = "硬件版本")
    private String hardwareVersion;

    @Schema(description = "设备状态（online/offline/maintenance）")
    private String deviceStatus;

    @Schema(description = "电池电量（0-100）")
    private Integer batteryLevel;

    @Schema(description = "信号强度")
    private Integer signalStrength;

    @Schema(description = "最后通信时间")
    private Long lastCommunicationTime;

    @Schema(description = "设备位置信息")
    private String location;

    @Schema(description = "绑定用户ID")
    private String userId;

    @Schema(description = "客户ID")
    private String customerId;

    @Schema(description = "组织ID")
    private String orgId;

    @Schema(description = "设备配置参数")
    private Map<String, Object> deviceConfig;

    @Schema(description = "网络连接信息")
    private Map<String, Object> networkInfo;

    @Schema(description = "传感器状态信息")
    private Map<String, Object> sensorStatus;

    @Schema(description = "批量设备信息列表")
    private List<DeviceInfoUploadRequest> batchDevices;

    @Schema(description = "设备注册时间")
    private Long registrationTime;

    @Schema(description = "扩展属性")
    private Map<String, Object> extraAttributes;

}