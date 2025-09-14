package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.modules.health.domain.dto.user.health.data.HealthDataAnalysisDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.ThresholdDTO;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.vo.HealthDataAnalysisVO;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataMapper;
import com.ljwx.modules.health.service.IHealthDataAnalysisService;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.ISysUserOrgService;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysUserOrg;
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
    private final ISysUserService sysUserService;
    private final ISysOrgUnitsService sysOrgUnitsService;
    private final ISysUserOrgService sysUserOrgService;
    
    /**
     * 用户信息内部类
     */
    private static class UserInfo {
        private String userId;
        private String userName;
        private String departmentId;
        private String departmentName;
        
        public UserInfo(String userId, String userName, String departmentId, String departmentName) {
            this.userId = userId;
            this.userName = userName;
            this.departmentId = departmentId;
            this.departmentName = departmentName;
        }
        
        // Getters
        public String getUserId() { return userId; }
        public String getUserName() { return userName; }
        public String getDepartmentId() { return departmentId; }
        public String getDepartmentName() { return departmentName; }
    }

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

        // 3. 直接使用userId查询，不再通过设备号
        List<Long> userIds = new ArrayList<>();
        if (analysisDTO.getUserIds() != null && !analysisDTO.getUserIds().isEmpty()) {
            // 直接使用提供的用户ID
            userIds.addAll(analysisDTO.getUserIds().stream()
                .map(Long::valueOf)
                .collect(Collectors.toList()));
        } else if (analysisDTO.getDepartmentIds() != null && !analysisDTO.getDepartmentIds().isEmpty()) {
            // 根据部门ID获取用户ID列表
            userIds.addAll(getUserIdsByDepartmentIds(analysisDTO.getDepartmentIds()));
        }
        
        if (!userIds.isEmpty()) {
            queryWrapper.in(TUserHealthData::getUserId, userIds);
        }

        // 4. 查询数据
        List<TUserHealthData> healthDataList = userHealthDataMapper.selectList(queryWrapper);

        // 5. 处理数据
        return processHealthData(healthDataList, analysisDTO);
    }

    /**
     * 根据部门ID列表获取用户ID列表
     */
    private List<Long> getUserIdsByDepartmentIds(List<String> departmentIds) {
        List<Long> deptIds = departmentIds.stream()
            .map(Long::valueOf)
            .collect(Collectors.toList());
        
        // 获取所有子部门ID（包括本身）
        List<Long> allDeptIds = new ArrayList<>(deptIds);
        for (Long deptId : deptIds) {
            List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(Collections.singletonList(deptId));
            allDeptIds.addAll(descendants.stream().map(SysOrgUnits::getId).collect(Collectors.toList()));
        }
        
        // 从 sys_user_org 获取所有用户ID
        List<Long> userIds = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .in(SysUserOrg::getOrgId, allDeptIds))
            .stream()
            .map(SysUserOrg::getUserId)
            .distinct()
            .collect(Collectors.toList());
            
        return userIds;
    }
    
    /**
     * 根据用户ID列表获取用户信息映射
     */
    private Map<Long, UserInfo> getUserInfoMap(List<Long> userIds) {
        Map<Long, UserInfo> result = new HashMap<>();
        if (userIds.isEmpty()) return result;
        
        // 1. 获取用户信息
        List<SysUser> users = sysUserService.list(new LambdaQueryWrapper<SysUser>()
            .in(SysUser::getId, userIds));
        
        // 2. 获取用户组织关系
        Map<Long, List<SysUserOrg>> userOrgMap = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .in(SysUserOrg::getUserId, userIds))
            .stream()
            .collect(Collectors.groupingBy(SysUserOrg::getUserId));
        
        // 3. 获取所有组织ID
        Set<Long> orgIds = userOrgMap.values().stream()
            .flatMap(List::stream)
            .map(SysUserOrg::getOrgId)
            .collect(Collectors.toSet());
        
        // 4. 获取组织信息映射
        Map<Long, SysOrgUnits> orgMap = sysOrgUnitsService.listByIds(orgIds)
            .stream()
            .collect(Collectors.toMap(SysOrgUnits::getId, org -> org));
        
        // 5. 组装用户信息
        for (SysUser user : users) {
            List<SysUserOrg> userOrgs = userOrgMap.getOrDefault(user.getId(), Collections.emptyList());
            String deptId = null;
            String deptName = null;
            
            if (!userOrgs.isEmpty()) {
                // 取第一个部门信息
                SysUserOrg userOrg = userOrgs.get(0);
                deptId = String.valueOf(userOrg.getOrgId());
                SysOrgUnits org = orgMap.get(userOrg.getOrgId());
                deptName = org != null ? org.getName() : null;
            }
            
            UserInfo userInfo = new UserInfo(
                String.valueOf(user.getId()),
                user.getUserName(),
                deptId,
                deptName
            );
            result.put(user.getId(), userInfo);
        }
        
        return result;
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
        Map<Long, UserInfo> userInfoMap = getUserInfoMap(
            healthDataList.stream()
                .map(TUserHealthData::getUserId)
                .filter(Objects::nonNull)
                .distinct()
                .collect(Collectors.toList())
        );

        // 3. 处理每条数据
        for (TUserHealthData data : healthDataList) {
            if (data.getUserId() == null) continue;
            UserInfo userInfo = userInfoMap.get(data.getUserId());
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
                                      UserInfo userInfo,
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
                                UserInfo userInfo,
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
                                   UserInfo userInfo,
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