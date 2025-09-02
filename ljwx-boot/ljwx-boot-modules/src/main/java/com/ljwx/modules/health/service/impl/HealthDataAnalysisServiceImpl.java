package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.modules.health.domain.dto.user.health.data.HealthDataAnalysisDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.ThresholdDTO;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.vo.HealthDataAnalysisVO;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataMapper;
import com.ljwx.modules.health.service.IDeviceUserMappingService;
import com.ljwx.modules.health.service.IHealthDataAnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class HealthDataAnalysisServiceImpl implements IHealthDataAnalysisService {

    private final TUserHealthDataMapper userHealthDataMapper;
    private final IDeviceUserMappingService deviceUserMappingService;

    @Override
    public HealthDataAnalysisVO analyzeHealthData(HealthDataAnalysisDTO analysisDTO) {
        // 1. 获取查询时间范围
        LocalDateTime startTime = LocalDateTime.ofInstant(
            Instant.ofEpochMilli(analysisDTO.getStartTime()),
            ZoneId.systemDefault()
        );
        LocalDateTime endTime = LocalDateTime.ofInstant(
            Instant.ofEpochMilli(analysisDTO.getEndTime()),
            ZoneId.systemDefault()
        );

        // 2. 构建查询条件
        LambdaQueryWrapper<TUserHealthData> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.between(TUserHealthData::getTimestamp, startTime, endTime);

        // 3. 获取设备号列表
        List<String> deviceSnList = new ArrayList<>();
        if (analysisDTO.getUserIds() != null && !analysisDTO.getUserIds().isEmpty()) {
            deviceSnList.addAll(deviceUserMappingService.getDeviceSnList(
                String.join(",", analysisDTO.getUserIds()),
                String.join(",", analysisDTO.getDepartmentIds())
            ));
        } else if (analysisDTO.getDepartmentIds() != null && !analysisDTO.getDepartmentIds().isEmpty()) {
            deviceSnList.addAll(deviceUserMappingService.getDeviceSnList(
                null,
                String.join(",", analysisDTO.getDepartmentIds())
            ));
        }
        
        if (!deviceSnList.isEmpty()) {
            queryWrapper.in(TUserHealthData::getDeviceSn, deviceSnList);
        }

        // 4. 查询数据
        List<TUserHealthData> healthDataList = userHealthDataMapper.selectList(queryWrapper);

        // 5. 处理数据
        return processHealthData(healthDataList, analysisDTO);
    }

    private HealthDataAnalysisVO processHealthData(List<TUserHealthData> healthDataList, HealthDataAnalysisDTO analysisDTO) {
        // 1. 初始化结果对象
        Map<String, List<HealthDataAnalysisVO.TimeSeriesDataPoint>> timeSeriesData = new HashMap<>();
        Map<String, HealthDataAnalysisVO.DepartmentStats> departmentStats = new HashMap<>();
        Map<String, HealthDataAnalysisVO.UserStats> userStats = new HashMap<>();
        HealthDataAnalysisVO.AbnormalStats abnormalStats = HealthDataAnalysisVO.AbnormalStats.builder()
            .abnormalByDataType(new HashMap<>())
            .abnormalByDepartment(new HashMap<>())
            .topAbnormalRecords(new ArrayList<>())
            .build();

        // 2. 获取用户和部门信息映射
        Map<String, IDeviceUserMappingService.UserInfo> deviceUserMap = deviceUserMappingService.getUserInfoMap(
            healthDataList.stream()
                .map(TUserHealthData::getDeviceSn)
                .filter(Objects::nonNull)
                .collect(Collectors.toList())
        );

        // 3. 处理每条数据
        for (TUserHealthData data : healthDataList) {
            IDeviceUserMappingService.UserInfo userInfo = deviceUserMap.get(data.getDeviceSn());
            if (userInfo == null) continue;

            // 3.1 处理时间序列数据
            processTimeSeriesData(data, timeSeriesData, analysisDTO.getTimeGranularity());

            // 3.2 处理部门统计
            processDepartmentStats(data, userInfo, departmentStats);

            // 3.3 处理用户统计
            processUserStats(data, userInfo, userStats);

            // 3.4 处理异常数据
            processAbnormalData(data, userInfo, analysisDTO.getThresholds(), abnormalStats);
        }

        // 4. 构建返回结果
        return HealthDataAnalysisVO.builder()
            .timeSeriesData(timeSeriesData)
            .departmentStats(departmentStats)
            .userStats(userStats)
            .abnormalStats(abnormalStats)
            .build();
    }

    private void processTimeSeriesData(TUserHealthData data, 
                                     Map<String, List<HealthDataAnalysisVO.TimeSeriesDataPoint>> timeSeriesData,
                                     String granularity) {
        // 根据时间粒度处理时间戳
        String timeKey = getTimeKey(data.getTimestamp(), granularity);
        
        // 处理各种数据类型
        processDataPoint(data.getHeartRate(), "heartRate", timeKey, timeSeriesData);
        processDataPoint(data.getBloodOxygen(), "bloodOxygen", timeKey, timeSeriesData);
        processDataPoint(data.getTemperature(), "temperature", timeKey, timeSeriesData);
        processDataPoint(data.getPressureHigh(), "pressureHigh", timeKey, timeSeriesData);
        processDataPoint(data.getPressureLow(), "pressureLow", timeKey, timeSeriesData);
        processDataPoint(data.getStep(), "step", timeKey, timeSeriesData);
    }

    private void processDataPoint(Number value, String dataType, String timeKey,
                                Map<String, List<HealthDataAnalysisVO.TimeSeriesDataPoint>> timeSeriesData) {
        if (value == null) return;
        
        String key = dataType + "_" + timeKey;
        timeSeriesData.computeIfAbsent(key, k -> new ArrayList<>())
            .add(HealthDataAnalysisVO.TimeSeriesDataPoint.builder()
                .timestamp(timeKey)
                .dataType(dataType)
                .avgValue(value.doubleValue())
                .maxValue(value.doubleValue())
                .minValue(value.doubleValue())
                .sampleCount(1)
                .build());
    }

    private void processDepartmentStats(TUserHealthData data,
                                      IDeviceUserMappingService.UserInfo userInfo,
                                      Map<String, HealthDataAnalysisVO.DepartmentStats> departmentStats) {
        String deptId = userInfo.getDepartmentId();
        HealthDataAnalysisVO.DepartmentStats stats = departmentStats.computeIfAbsent(deptId,
            k -> HealthDataAnalysisVO.DepartmentStats.builder()
                .departmentId(deptId)
                .departmentName(userInfo.getDepartmentName())
                .dataTypeStats(new HashMap<>())
                .totalEmployees(0)
                .activeEmployees(0)
                .build());

        // 更新部门统计数据
        updateAggregateStats(stats.getDataTypeStats(), "heartRate", data.getHeartRate());
        updateAggregateStats(stats.getDataTypeStats(), "bloodOxygen", data.getBloodOxygen());
        updateAggregateStats(stats.getDataTypeStats(), "temperature", data.getTemperature());
        updateAggregateStats(stats.getDataTypeStats(), "pressureHigh", data.getPressureHigh());
        updateAggregateStats(stats.getDataTypeStats(), "pressureLow", data.getPressureLow());
        updateAggregateStats(stats.getDataTypeStats(), "step", data.getStep());
    }

    private void processUserStats(TUserHealthData data,
                                IDeviceUserMappingService.UserInfo userInfo,
                                Map<String, HealthDataAnalysisVO.UserStats> userStats) {
        String userId = userInfo.getUserId();
        HealthDataAnalysisVO.UserStats stats = userStats.computeIfAbsent(userId,
            k -> HealthDataAnalysisVO.UserStats.builder()
                .userId(userId)
                .userName(userInfo.getUserName())
                .departmentId(userInfo.getDepartmentId())
                .dataTypeStats(new HashMap<>())
                .dataPoints(0)
                .complianceRate(0.0)
                .build());

        // 更新用户统计数据
        stats.setDataPoints(stats.getDataPoints() + 1);
        updateAggregateStats(stats.getDataTypeStats(), "heartRate", data.getHeartRate());
        updateAggregateStats(stats.getDataTypeStats(), "bloodOxygen", data.getBloodOxygen());
        updateAggregateStats(stats.getDataTypeStats(), "temperature", data.getTemperature());
        updateAggregateStats(stats.getDataTypeStats(), "pressureHigh", data.getPressureHigh());
        updateAggregateStats(stats.getDataTypeStats(), "pressureLow", data.getPressureLow());
        updateAggregateStats(stats.getDataTypeStats(), "step", data.getStep());
    }

    private void processAbnormalData(TUserHealthData data,
                                   IDeviceUserMappingService.UserInfo userInfo,
                                   List<ThresholdDTO> thresholds,
                                   HealthDataAnalysisVO.AbnormalStats abnormalStats) {
        if (thresholds == null) return;

        for (ThresholdDTO threshold : thresholds) {
            Double value = getDataValue(data, threshold.getDataType());
            if (value == null) continue;

            if (value < threshold.getMinThreshold() || value > threshold.getMaxThreshold()) {
                // 更新异常计数
                abnormalStats.getAbnormalByDataType().merge(threshold.getDataType(), 1, Integer::sum);
                abnormalStats.getAbnormalByDepartment().merge(userInfo.getDepartmentId(), 1, Integer::sum);

                // 添加异常记录
                abnormalStats.getTopAbnormalRecords().add(
                    HealthDataAnalysisVO.AbnormalRecord.builder()
                        .userId(userInfo.getUserId())
                        .userName(userInfo.getUserName())
                        .departmentId(userInfo.getDepartmentId())
                        .dataType(threshold.getDataType())
                        .value(value)
                        .timestamp(data.getTimestamp().toString())
                        .build()
                );
            }
        }
    }

    private void updateAggregateStats(Map<String, HealthDataAnalysisVO.AggregateStats> statsMap,
                                    String dataType,
                                    Number value) {
        if (value == null) return;

        HealthDataAnalysisVO.AggregateStats stats = statsMap.computeIfAbsent(dataType,
            k -> HealthDataAnalysisVO.AggregateStats.builder()
                .avgValue(0.0)
                .maxValue(Double.MIN_VALUE)
                .minValue(Double.MAX_VALUE)
                .stdDev(0.0)
                .sampleCount(0)
                .abnormalCount(0)
                .build());

        double doubleValue = value.doubleValue();
        stats.setMaxValue(Math.max(stats.getMaxValue(), doubleValue));
        stats.setMinValue(Math.min(stats.getMinValue(), doubleValue));
        stats.setSampleCount(stats.getSampleCount() + 1);
        
        // 更新平均值
        double oldAvg = stats.getAvgValue();
        int n = stats.getSampleCount();
        stats.setAvgValue(oldAvg + (doubleValue - oldAvg) / n);
        
        // 更新标准差（使用Welford在线算法）
        if (n > 1) {
            double oldS = stats.getStdDev() * stats.getStdDev() * (n - 1);
            double newS = oldS + (doubleValue - oldAvg) * (doubleValue - stats.getAvgValue());
            stats.setStdDev(Math.sqrt(newS / (n - 1)));
        }
    }

    private String getTimeKey(LocalDateTime timestamp, String granularity) {
        switch (granularity.toLowerCase()) {
            case "hour":
                return timestamp.truncatedTo(ChronoUnit.HOURS).toString();
            case "day":
                return timestamp.truncatedTo(ChronoUnit.DAYS).toString();
            case "week":
                return timestamp.truncatedTo(ChronoUnit.WEEKS).toString();
            case "month":
                return timestamp.truncatedTo(ChronoUnit.MONTHS).toString();
            default:
                return timestamp.toString();
        }
    }

    private Double getDataValue(TUserHealthData data, String dataType) {
        switch (dataType) {
            case "heartRate":
                return data.getHeartRate() != null ? data.getHeartRate().doubleValue() : null;
            case "bloodOxygen":
                return data.getBloodOxygen() != null ? data.getBloodOxygen().doubleValue() : null;
            case "temperature":
                return data.getTemperature();
            case "pressureHigh":
                return data.getPressureHigh() != null ? data.getPressureHigh().doubleValue() : null;
            case "pressureLow":
                return data.getPressureLow() != null ? data.getPressureLow().doubleValue() : null;
            case "step":
                return data.getStep() != null ? data.getStep().doubleValue() : null;
            default:
                return null;
        }
    }
} 