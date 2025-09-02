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

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 健康数据上传请求DTO
 * 
 * 兼容ljwx-bigscreen的健康数据格式，支持嵌套data结构和underscore命名
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName HealthDataUploadRequest
 * @CreateTime 2024-12-16
 */
@Data
@Schema(description = "健康数据上传请求")
public class HealthDataUploadRequest {

    @Schema(description = "嵌套的健康数据")
    private HealthDataItem data;

    @Schema(description = "批量健康数据列表")
    @JsonProperty("batch_data")
    private List<HealthDataUploadRequest> batchData;

    /**
     * 健康数据项内部类
     */
    @Data
    @Schema(description = "健康数据项")
    public static class HealthDataItem {

        @Schema(description = "设备序列号")
        private String deviceSn;

        @Schema(description = "客户ID")
        @JsonProperty("customer_id")
        private String customerId;

        @Schema(description = "用户ID")
        @JsonProperty("user_id")
        private String userId;

        @Schema(description = "组织ID")
        @JsonProperty("org_id")
        private String orgId;

        @Schema(description = "数据时间戳")
        private Long timestamp;

        @Schema(description = "心率")
        @JsonProperty("heart_rate")
        private Integer heartRate;

        @Schema(description = "血氧")
        @JsonProperty("blood_oxygen")
        private Integer bloodOxygen;

        @Schema(description = "体温")
        @JsonProperty("body_temperature")
        private Double bodyTemperature;

        @Schema(description = "收缩压")
        @JsonProperty("blood_pressure_systolic")
        private Integer bloodPressureSystolic;

        @Schema(description = "舒张压")
        @JsonProperty("blood_pressure_diastolic")
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
        @JsonProperty("sleep_quality")
        private Integer sleepQuality;

        @Schema(description = "运动强度")
        @JsonProperty("exercise_intensity")
        private Integer exerciseIntensity;

        @Schema(description = "扩展数据字段")
        @JsonProperty("extra_data")
        private Map<String, Object> extraData;

        @Schema(description = "数据来源类型")
        @JsonProperty("source_type")
        private String sourceType;

        @Schema(description = "数据版本")
        @JsonProperty("data_version")
        private String dataVersion;
    }

    // 便捷访问方法，保持向后兼容
    public String getDeviceSn() {
        return data != null ? data.getDeviceSn() : null;
    }

    public String getCustomerId() {
        return data != null ? data.getCustomerId() : null;
    }

    public String getUserId() {
        return data != null ? data.getUserId() : null;
    }

    public String getOrgId() {
        return data != null ? data.getOrgId() : null;
    }

    public Long getTimestamp() {
        return data != null ? data.getTimestamp() : null;
    }

    public Integer getHeartRate() {
        return data != null ? data.getHeartRate() : null;
    }

    public Integer getBloodOxygen() {
        return data != null ? data.getBloodOxygen() : null;
    }

    public Double getBodyTemperature() {
        return data != null ? data.getBodyTemperature() : null;
    }

    public Integer getBloodPressureSystolic() {
        return data != null ? data.getBloodPressureSystolic() : null;
    }

    public Integer getBloodPressureDiastolic() {
        return data != null ? data.getBloodPressureDiastolic() : null;
    }

    public Integer getStep() {
        return data != null ? data.getStep() : null;
    }

    public Integer getDistance() {
        return data != null ? data.getDistance() : null;
    }

    public Integer getCalorie() {
        return data != null ? data.getCalorie() : null;
    }

    public Double getLatitude() {
        return data != null ? data.getLatitude() : null;
    }

    public Double getLongitude() {
        return data != null ? data.getLongitude() : null;
    }

    public Integer getStress() {
        return data != null ? data.getStress() : null;
    }

    public Integer getSleepQuality() {
        return data != null ? data.getSleepQuality() : null;
    }

    public Integer getExerciseIntensity() {
        return data != null ? data.getExerciseIntensity() : null;
    }

    public Map<String, Object> getExtraData() {
        return data != null ? data.getExtraData() : null;
    }

    public String getSourceType() {
        return data != null ? data.getSourceType() : null;
    }

    public String getDataVersion() {
        return data != null ? data.getDataVersion() : null;
    }

}