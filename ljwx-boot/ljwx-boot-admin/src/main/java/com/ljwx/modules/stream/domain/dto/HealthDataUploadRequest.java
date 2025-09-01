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
 * 健康数据上传请求DTO
 * 
 * 兼容ljwx-bigscreen的健康数据格式，支持单条和批量数据上传
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName HealthDataUploadRequest
 * @CreateTime 2024-12-16
 */
@Data
@Schema(description = "健康数据上传请求")
public class HealthDataUploadRequest {

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "客户ID")
    private String customerId;

    @Schema(description = "用户ID")
    private String userId;

    @Schema(description = "组织ID")
    private String orgId;

    @Schema(description = "数据时间戳")
    private Long timestamp;

    @Schema(description = "心率")
    private Integer heartRate;

    @Schema(description = "血氧")
    private Integer bloodOxygen;

    @Schema(description = "体温")
    private Double bodyTemperature;

    @Schema(description = "收缩压")
    private Integer bloodPressureSystolic;

    @Schema(description = "舒张压")
    private Integer bloodPressureDiastolic;

    @Schema(description = "步数")
    private Integer step;

    @Schema(description = "距离(米)")
    private Integer distance;

    @Schema(description = "卡路里")
    private Integer calorie;

    @Schema(description = "纬度")
    private Double latitude;

    @Schema(description = "经度")
    private Double longitude;

    @Schema(description = "压力值")
    private Integer stress;

    @Schema(description = "睡眠质量分数")
    private Integer sleepQuality;

    @Schema(description = "运动强度")
    private Integer exerciseIntensity;

    @Schema(description = "批量健康数据列表")
    private List<HealthDataUploadRequest> batchData;

    @Schema(description = "扩展数据字段")
    private Map<String, Object> extraData;

    @Schema(description = "数据来源类型")
    private String sourceType;

    @Schema(description = "数据版本")
    private String dataVersion;

}