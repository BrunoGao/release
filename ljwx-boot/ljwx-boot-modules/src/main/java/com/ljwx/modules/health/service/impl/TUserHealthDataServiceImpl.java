/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
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

package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataSearchDTO;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.entity.TUserHealthDataDaily;
import com.ljwx.modules.health.domain.entity.TUserHealthDataWeekly;
import com.ljwx.modules.health.domain.vo.HealthDataPageVO;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataMapper;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataDailyMapper;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataWeeklyMapper;
import com.ljwx.modules.health.service.IDeviceUserMappingService;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.health.util.HealthDataTableUtil;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneOffset;
import java.time.temporal.ChronoField;
import java.util.*;
import java.util.stream.Collectors;

/**
 *  Service 服务接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TUserHealthDataServiceImpl
 * @CreateTime 2024-12-15 - 22:04:51
 */

@Service
@Slf4j
public class TUserHealthDataServiceImpl extends ServiceImpl<TUserHealthDataMapper, TUserHealthData> implements ITUserHealthDataService {

    @Autowired
    private IDeviceUserMappingService deviceUserMappingService;

    @Autowired
    private ITHealthDataConfigService healthDataConfigService;  // 从 customer 模块注入

    @Autowired
    private TUserHealthDataDailyMapper dailyMapper; // #每日数据Mapper

    @Autowired
    private TUserHealthDataWeeklyMapper weeklyMapper; // #每周数据Mapper

    @Autowired
    private ISysUserService sysUserService;

    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * 获取过滤管理员后的设备列表 #管理员过滤功能
     * @param userId 用户ID
     * @param departmentInfo 部门信息
     * @return 过滤后的设备序列号列表
     */
    private List<String> getFilteredDeviceSnList(String userId, String departmentInfo) {
        // 如果指定了具体用户ID且不是"all"、"0"或空，直接查询该用户设备
        if (ObjectUtils.isNotEmpty(userId) && !"all".equals(userId) && !"0".equals(userId)) {
            return deviceUserMappingService.getDeviceSnList(userId, departmentInfo);
        }
        
        // 查询部门设备时，需要过滤管理员设备
        if (ObjectUtils.isNotEmpty(departmentInfo)) {
            System.out.println("🔍 查询部门设备: departmentInfo=" + departmentInfo);
            List<String> allDeviceSnList = deviceUserMappingService.getDeviceSnList(null, departmentInfo);
            System.out.println("📱 部门所有设备数量: " + allDeviceSnList.size() + ", 设备列表: " + allDeviceSnList);
            if (allDeviceSnList.isEmpty()) {
                System.out.println("⚠️ 部门设备列表为空，返回空结果");
                return Collections.emptyList();
            }
            
            // 获取管理员设备列表
            List<String> adminDeviceSnList = getAdminDeviceSnList();
            System.out.println("🔒 管理员设备列表: " + adminDeviceSnList);
            
            // 过滤掉管理员设备
            List<String> filteredList = allDeviceSnList.stream()
                .filter(deviceSn -> !adminDeviceSnList.contains(deviceSn))
                .collect(Collectors.toList());
            
            System.out.println("📊 过滤前设备数: " + allDeviceSnList.size() + ", 过滤后设备数: " + filteredList.size());
            return filteredList;
        }
        
        return Collections.emptyList();
    }

    /**
     * 获取管理员设备序列号列表 #管理员设备识别
     * @return 管理员设备序列号列表
     */
    private List<String> getAdminDeviceSnList() {
        try {
            return sysUserService.list().stream()
                .filter(user -> sysUserService.isAdminUser(user.getId()))
                .map(SysUser::getDeviceSn)
                .filter(Objects::nonNull)
                .filter(deviceSn -> !deviceSn.trim().isEmpty())
                .collect(Collectors.toList());
        } catch (Exception e) {
            System.err.println("❌ 获取管理员设备列表失败: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    @Override
    public HealthDataPageVO<Map<String,Object>> listTUserHealthDataPage(PageQuery pageQuery, TUserHealthDataSearchDTO tUserHealthDataBO) {
        // 1. 时间边界
    LocalDateTime startDate = LocalDateTime.ofEpochSecond(
        tUserHealthDataBO.getStartDate() / 1000, 0, ZoneOffset.ofHours(8));
    LocalDateTime endDate = LocalDateTime.ofEpochSecond(
        (tUserHealthDataBO.getEndDate() + 86399000) / 1000, 0, ZoneOffset.ofHours(8));

    // 2. 拿到所有要查询的设备 SN - 自动过滤管理员设备
    System.out.println("🏥 健康数据查询 - userId: " + tUserHealthDataBO.getUserId() + ", departmentInfo: " + tUserHealthDataBO.getDepartmentInfo());
    
    // 3. 基础 Wrapper
    LambdaQueryWrapper<TUserHealthData> query = new LambdaQueryWrapper<>();
    
    // 如果指定了具体用户，获取该用户指定时间范围内的所有数据
    if (ObjectUtils.isNotEmpty(tUserHealthDataBO.getUserId()) && 
        !"0".equals(tUserHealthDataBO.getUserId()) && 
        !"all".equals(tUserHealthDataBO.getUserId())) {
        
        System.out.println("🔍 查询指定用户时间范围内所有数据: userId=" + tUserHealthDataBO.getUserId());
        
        List<String> deviceSnList = getFilteredDeviceSnList(
            tUserHealthDataBO.getUserId(),
            tUserHealthDataBO.getDepartmentInfo()
        );
        if (deviceSnList.isEmpty()) {
            System.out.println("⚠️ 未找到符合条件的设备，返回空结果");
            return new HealthDataPageVO<>(
                Collections.emptyList(),
                0, pageQuery.getPageSize(), pageQuery.getPage(),
                Collections.emptyList()
            );
        }
        System.out.println("✅ 获取到设备列表: " + deviceSnList);
        
        // 查询该用户指定时间范围内的所有数据
        query.ge(TUserHealthData::getTimestamp, startDate)
             .le(TUserHealthData::getTimestamp, endDate)
             .in(TUserHealthData::getDeviceSn, deviceSnList);
             
    } else {
        // 如果没有指定具体用户（userId为空、"0"或"all"），只查询部门下所有设备的最新数据
        System.out.println("🔍 查询部门所有设备最新数据");
        
        // 获取部门下所有设备（已经过滤了管理员设备）
        List<String> deviceSnList = getFilteredDeviceSnList(null, tUserHealthDataBO.getDepartmentInfo());
        if (deviceSnList.isEmpty()) {
            System.out.println("⚠️ 部门下未找到任何设备，返回空结果");
            return new HealthDataPageVO<>(
                Collections.emptyList(),
                0, pageQuery.getPageSize(), pageQuery.getPage(),
                Collections.emptyList()
            );
        }
        
        System.out.println("✅ 获取到部门设备列表: " + deviceSnList);
        
        // 先查询指定时间范围内的所有数据
        LambdaQueryWrapper<TUserHealthData> tempQuery = new LambdaQueryWrapper<>();
        tempQuery.ge(TUserHealthData::getTimestamp, startDate)
                 .le(TUserHealthData::getTimestamp, endDate)
                 .in(TUserHealthData::getDeviceSn, deviceSnList);
                 
        List<TUserHealthData> allData = baseMapper.selectList(tempQuery);
        System.out.println("📊 查询到原始数据条数: " + allData.size());
        
        if (allData.isEmpty()) {
            return new HealthDataPageVO<>(
                Collections.emptyList(),
                0, pageQuery.getPageSize(), pageQuery.getPage(),
                Collections.emptyList()
            );
        }
        
        // 按设备分组，获取每个设备的最新数据
        Map<String, TUserHealthData> latestByDevice = allData.stream()
            .collect(Collectors.toMap(
                TUserHealthData::getDeviceSn,
                data -> data,
                (existing, replacement) -> existing.getTimestamp().isAfter(replacement.getTimestamp()) ? existing : replacement
            ));
            
        System.out.println("📱 设备数量: " + latestByDevice.size());
        
        // 获取最新数据的ID列表，重新构建查询条件
        List<Long> latestIds = latestByDevice.values().stream()
            .map(TUserHealthData::getId)
            .collect(Collectors.toList());
        query = new LambdaQueryWrapper<>();
        query.in(TUserHealthData::getId, latestIds);
    }
    
    query.orderByDesc(TUserHealthData::getTimestamp);

        IPage<TUserHealthData> page = baseMapper.selectPage(pageQuery.buildPage(), query);
        
        // 调试信息：显示查询结果统计
        System.out.println("📋 分页查询结果统计:");
        System.out.println("  总记录数: " + page.getTotal());
        System.out.println("  当前页记录数: " + page.getRecords().size());
        System.out.println("  当前页码: " + page.getCurrent());
        System.out.println("  每页大小: " + page.getSize());

        // 获取所有不重复的deviceSn
        Set<String> deviceSns = page.getRecords().stream()
            .map(TUserHealthData::getDeviceSn)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        // 获取设备关联的用户和部门信息
        Map<String, IDeviceUserMappingService.UserInfo> deviceUserMap = deviceUserMappingService.getDeviceUserInfo(deviceSns);

        // 为每条记录添加用户和部门信息
        page.getRecords().forEach(record -> {
            if (record.getDeviceSn() != null) {
                IDeviceUserMappingService.UserInfo userInfo = deviceUserMap.get(record.getDeviceSn());
                if (userInfo != null) {
                    record.setUserName(userInfo.getUserName());
                    record.setDepartmentInfo(userInfo.getDepartmentName());
                }
                //record.setSleepData(processSleepData(record.getSleepData().toString()));
                //record.setWorkoutData(processWorkoutData(record.getWorkoutData().toString()));
                //record.setExerciseDailyData(processExerciseDailyData(record.getExerciseDailyData().toString()));
            }
        });
                       

        // 根据departmentInfo查询顶级部门ID，用于过滤health data config
        Long topLevelDeptId = null;
        if (ObjectUtils.isNotEmpty(tUserHealthDataBO.getDepartmentInfo())) {
            try {
                Long deptId = Long.parseLong(tUserHealthDataBO.getDepartmentInfo());
                topLevelDeptId = sysOrgUnitsService.getTopLevelDeptIdByOrgId(deptId);
                System.out.println("🏢 部门查询 - departmentInfo: " + deptId + " -> 顶级部门ID: " + topLevelDeptId);
            } catch (NumberFormatException e) {
                System.err.println("❌ departmentInfo格式错误: " + tUserHealthDataBO.getDepartmentInfo());
                topLevelDeptId = null;
            }
        }
        
        // 使用新的服务方法获取启用的健康数据配置
        Long orgIdForQuery = topLevelDeptId != null ? topLevelDeptId : Long.parseLong(tUserHealthDataBO.getDepartmentInfo());
        List<THealthDataConfig> enabledColumns = healthDataConfigService.getEnabledConfigsByOrgId(orgIdForQuery);

        // 批量获取分表数据（避免n+1问题）
        // 根据查询类型决定是否需要批量获取分表数据
        final Map<String, Map<String, Object>> batchDailyData;
        final Map<String, Map<String, Object>> batchWeeklyData;
        
        // 只有在查询结果不为空时才批量获取分表数据
        if (!page.getRecords().isEmpty()) {
            batchDailyData = getBatchDailyData(page.getRecords());
            batchWeeklyData = getBatchWeeklyData(page.getRecords());
        } else {
            batchDailyData = new HashMap<>();
            batchWeeklyData = new HashMap<>();
        }

        List<Map<String, Object>> records = page.getRecords().stream()
    .map(record -> {
        Map<String, Object> filteredData = new HashMap<>();

        // 基础字段
        filteredData.put("id", record.getId());
        filteredData.put("timestamp", record.getTimestamp());
        filteredData.put("deviceSn", record.getDeviceSn());

        // 用户信息
        if (record.getDeviceSn() != null) {
            IDeviceUserMappingService.UserInfo userInfo = deviceUserMap.get(record.getDeviceSn());
            if (userInfo != null) {
                filteredData.put("userName", userInfo.getUserName());
                filteredData.put("departmentInfo", userInfo.getDepartmentName());
            }
        }

        // 批量获取分表数据（避免n+1问题）
        // 这些数据会在后面统一批量获取
        String cacheKey = record.getDeviceSn() + "_" + record.getTimestamp().toLocalDate();
        Map<String, Object> dailyData = batchDailyData.getOrDefault(cacheKey, Collections.emptyMap());
        Map<String, Object> weeklyData = batchWeeklyData.getOrDefault(cacheKey, Collections.emptyMap());

        // 启用字段动态处理
        for (THealthDataConfig config : enabledColumns) {
            String fieldName = config.getDataType();
            Object value = getFieldValue(record, fieldName);
            Object processed = null;
            System.out.println("fieldName::" + fieldName + "=" + value);

            switch (fieldName) {
                case "sleep":
                    processed = processSleepData((String) dailyData.get("sleepData"));
                    filteredData.put("sleepData", processed);
                    break;
                case "work_out":
                    processed = processWorkoutData((String) dailyData.get("workoutData"));
                    filteredData.put("workoutData", processed);
                    break;
                case "exercise_daily":
                    processed = processExerciseDailyData((String) dailyData.get("exerciseDailyData"));
                    filteredData.put("exerciseDailyData", processed);
                    break;
                case "exercise_week":
                    processed = processExerciseWeekData((String) weeklyData.get("exerciseWeekData"));
                    filteredData.put("exerciseWeekData", processed);
                    break;
                case "blood_oxygen":
                    filteredData.put("bloodOxygen", value);
                    break;
                case "heart_rate":
                    if (value != null) {
                        filteredData.put("heartRate", value);
                        filteredData.put("pressureHigh", getFieldValue(record, "pressure_high"));
                        filteredData.put("pressureLow", getFieldValue(record, "pressure_low"));
                    }
                    break;
                case "location":
                   
                    filteredData.put("latitude",  getFieldValue(record, "latitude"));
                    filteredData.put("longitude", getFieldValue(record, "longitude"));
                    filteredData.put("altitude", getFieldValue(record, "altitude"));
                    
                    break;
                default:
                    // 普通字段原样放入
                    if (value != null) {
                        filteredData.put(fieldName, value);
                    }
                    break;
            }

            // 若以上 JSON 类型字段为空，也确保返回结构体格式
            if ((processed == null || ((Map<?, ?>) processed).isEmpty()) &&
                Set.of("sleep", "work_out", "exercise_daily", "exercise_week").contains(fieldName)) {
                String mappedField = switch (fieldName) {
                    case "sleep" -> "sleepData";
                    case "work_out" -> "workoutData";
                    case "exercise_daily" -> "exerciseDailyData";
                    case "exercise_week" -> "exerciseWeekData";
                    default -> fieldName;
                };
                filteredData.put(mappedField, Map.of("value", "-", "tooltip", "当前暂无数据"));
            }
        }

                return filteredData;
            })
            .collect(Collectors.toList());

        System.out.println("最终返回records: " + records);
        

        // 5. 构建返回结果
        Map<String, Object> result = new HashMap<>();
        result.put("columns", enabledColumns);  // 返回列配置信息
        result.put("total", page.getTotal());
        result.put("size", page.getSize());
        result.put("current", page.getCurrent());
        result.put("records", records);         // 返回过滤后的数据

        // 创建包含列信息的分页对象
        return new HealthDataPageVO<>(records, page.getTotal(), page.getSize(), page.getCurrent(), enabledColumns);
    }

    private Object getFieldValue(TUserHealthData record, String fieldName) {
        System.out.println("getFieldValue::" + fieldName);
        return switch (fieldName) {
            case "blood_oxygen" -> record.getBloodOxygen();
            case "heart_rate" -> record.getHeartRate();
            case "pressure_high" -> record.getPressureHigh();
            case "pressure_low" -> record.getPressureLow();
            case "step" -> record.getStep();
            case "temperature" -> record.getTemperature();
            case "sleep", "work_out", "exercise_daily", "exercise_week" -> null; // #这些字段已迁移到分表
            case "stress" -> record.getStress();
            case "distance" -> record.getDistance();
            case "calorie" -> record.getCalorie();
            case "latitude" -> record.getLatitude();
            case "longitude" -> record.getLongitude();
            case "altitude" -> record.getAltitude();
            default -> null;
        };
    }

    @Override
    public ResponseEntity<Object> getUserHealthData(String departmentInfo, String userId, LocalDateTime startDate, LocalDateTime endDate, String timeType) {
        List<String> deviceSnList = deviceUserMappingService.getDeviceSnList(userId, departmentInfo);
        System.out.println("getUserHealthData::" + startDate + "::" + endDate + "::" + deviceSnList);
        
        if (deviceSnList.isEmpty()) {
            return ResponseEntity.ok(Map.of("data", Map.of(), "code", "200", "msg", "无设备数据"));
        }
        
        // 优化：直接查询主表数据，避免分表查询性能问题
        List<TUserHealthData> data = getOptimizedHealthData(deviceSnList, startDate, endDate);
        System.out.println("getUserHealthData::" + data.size());

        Map<String, Object> jsonData = new TreeMap<>(Comparator.naturalOrder());

        if ("day".equalsIgnoreCase(timeType)) {
            // 按小时分组
            Map<LocalDateTime, List<TUserHealthData>> groupedByDayHour = data.stream()
                    .collect(Collectors.groupingBy(record -> record.getTimestamp().withMinute(0).withSecond(0).withNano(0)));

            LocalDateTime currentHour = startDate.withMinute(0).withSecond(0).withNano(0);
            LocalDateTime endHour = endDate.withMinute(0).withSecond(0).withNano(0);

            // 遍历每小时，填充数据
            while (!currentHour.isAfter(endHour)) {
                List<TUserHealthData> records = groupedByDayHour.getOrDefault(currentHour, Collections.emptyList());
                List<Map<String, Object>> hourData = records.stream().map(this::mapHealthData).collect(Collectors.toList());
                jsonData.put(currentHour.toString(), hourData);
                currentHour = currentHour.plusHours(1);
            }
        } else if ("week".equalsIgnoreCase(timeType)) {
            // 按天分组
            Map<LocalDate, List<TUserHealthData>> groupedByDay = data.stream()
                    .collect(Collectors.groupingBy(record -> record.getTimestamp().toLocalDate()));

            // 遍历每一天，计算每小时的平均值
            groupedByDay.forEach((day, records) -> {
                Map<LocalTime, List<TUserHealthData>> groupedByHour = records.stream()
                        .collect(Collectors.groupingBy(record -> record.getTimestamp().toLocalTime().withMinute(0).withSecond(0).withNano(0)));

                Map<String, Object> dayAverage = new HashMap<>();
                groupedByHour.forEach((hour, hourlyRecords) -> {
                    Map<String, Object> hourAverage = calculateAverage(hourlyRecords);
                    dayAverage.put(hour.toString(), hourAverage);
                });

                jsonData.put(day.toString(), dayAverage);
            });
        } else if ("month".equalsIgnoreCase(timeType)) {
            // 按天分组
            Map<LocalDate, List<TUserHealthData>> groupedByDay = data.stream()
                    .collect(Collectors.groupingBy(record -> record.getTimestamp().toLocalDate()));

            // 遍历每一天，计算平均值
            groupedByDay.forEach((day, records) -> {
                Map<String, Object> dayAverage = calculateAverage(records);
                jsonData.put(day.toString(), dayAverage);
            });
        } else if ("year".equalsIgnoreCase(timeType)) {
            // 按年+周分组
            Map<String, List<TUserHealthData>> groupedByYearWeek = data.stream()
                .collect(Collectors.groupingBy(record -> {
                    LocalDateTime ts = record.getTimestamp();
                    return ts.getYear() + "-W" + String.format("%02d", ts.get(ChronoField.ALIGNED_WEEK_OF_YEAR));
                }));
        
            // 排序并生成有序结果
            Map<String, Object> orderedJsonData = groupedByYearWeek.entrySet().stream()
                .sorted(Comparator.comparing(entry -> {
                    String[] arr = entry.getKey().split("-W");
                    int year = Integer.parseInt(arr[0]);
                    int week = Integer.parseInt(arr[1]);
                    return year * 100 + week;
                }))
                .collect(Collectors.toMap(
                    Map.Entry::getKey,
                    entry -> calculateAverage(entry.getValue()),
                    (a, b) -> a,
                    LinkedHashMap::new
                ));
        
            jsonData.clear();
            jsonData.putAll(orderedJsonData);
        }

        Map<String, Object> response = new HashMap<>();
        response.put("data", jsonData);
        response.put("code", "200");
        response.put("msg", "操作成功");

        return ResponseEntity.ok(response);
    }

    private Map<String, Object> mapHealthData(TUserHealthData r) { // #null给0
        Map<String, Object> m = new HashMap<>();
        m.put("bloodOxygen", String.valueOf(r.getBloodOxygen() == null ? 0 : r.getBloodOxygen()));
        m.put("heartRate", String.valueOf(r.getHeartRate() == null ? 0 : r.getHeartRate()));
        m.put("pressureHigh", String.valueOf(r.getPressureHigh() == null ? 0 : r.getPressureHigh()));
        m.put("pressureLow", String.valueOf(r.getPressureLow() == null ? 0 : r.getPressureLow()));
        m.put("step", String.valueOf(r.getStep() == null ? 0 : r.getStep()));
        m.put("temperature", String.format("%.2f", r.getTemperature() == null ? 0.0 : r.getTemperature()));
        m.put("timestamp", r.getTimestamp() == null ? "0" : r.getTimestamp().toString());
        m.put("sleep", "0"); // #睡眠数据已迁移到分表，暂时返回默认值
        m.put("stress", String.valueOf(r.getStress() == null ? 0 : r.getStress()));
        m.put("distance", String.valueOf(r.getDistance() == null ? 0 : r.getDistance()));
        m.put("calorie", String.valueOf(r.getCalorie() == null ? 0 : r.getCalorie()));
        return m;
    }

    private Map<String, Object> mapHealthDataWithShardedData(TUserHealthData r) { // #包含分表数据的映射
        Map<String, Object> m = mapHealthData(r); // #复用基础映射
        
        // 获取分表数据
        Map<String, Object> dailyData = getDailyData(r.getDeviceSn(), r.getTimestamp());
        String sleepDataStr = (String) dailyData.get("sleepData");
        if (sleepDataStr != null) {
            Map<String, Object> sleepResult = processSleepData(sleepDataStr);
            m.put("sleep", sleepResult.get("value"));
        }
        
        return m;
    }

    private Map<String, Object> calculateAverage(List<TUserHealthData> records) {
        Map<String, Object> averages = new HashMap<>();
        if (records == null || records.isEmpty()) {
            return averages;
        }

        try {
            // 心率
            OptionalDouble heartRateAvg = records.stream()
                .filter(r -> r.getHeartRate() != null)
                .mapToInt(TUserHealthData::getHeartRate)
                .average();
            if (heartRateAvg.isPresent()) {
                averages.put("heartRate", Math.round(heartRateAvg.getAsDouble()));
            }

            // 血氧
            OptionalDouble spo2Avg = records.stream()
                .filter(r -> r.getBloodOxygen() != null)
                .mapToInt(TUserHealthData::getBloodOxygen)
                .average();
            if (spo2Avg.isPresent()) {
                averages.put("bloodOxygen", Math.round(spo2Avg.getAsDouble()));
            }

            // 体温
            OptionalDouble temperatureAvg = records.stream()
                .filter(r -> r.getTemperature() != null)
                .mapToDouble(TUserHealthData::getTemperature)
                .average();
            if (temperatureAvg.isPresent()) {
                averages.put("temperature", Math.round(temperatureAvg.getAsDouble() * 10.0) / 10.0);
            }

            // 步数
            OptionalDouble stepAvg = records.stream()
                .filter(r -> r.getStep() != null)
                .mapToInt(TUserHealthData::getStep)
                .average();
            if (stepAvg.isPresent()) {
                averages.put("step", Math.round(stepAvg.getAsDouble()));
            }

            // 高压
            OptionalDouble pressureHighAvg = records.stream()
                .filter(r -> r.getPressureHigh() != null)
                .mapToInt(TUserHealthData::getPressureHigh)
                .average();
            if (pressureHighAvg.isPresent()) {
                averages.put("pressureHigh", Math.round(pressureHighAvg.getAsDouble()));
            }

            // 低压
            OptionalDouble pressureLowAvg = records.stream()
                .filter(r -> r.getPressureLow() != null)
                .mapToInt(TUserHealthData::getPressureLow)
                .average();
            if (pressureLowAvg.isPresent()) {
                averages.put("pressureLow", Math.round(pressureLowAvg.getAsDouble()));
            }

        } catch (Exception e) {
            log.error("Error calculating averages: ", e);
        }

        return averages;
    }

    private void processTimeGroupedData(String timeType, List<TUserHealthData> data, Map<String, Object> jsonData) {
        if (data == null || data.isEmpty()) {
            return;
        }

        try {
            if ("week".equalsIgnoreCase(timeType)) {
                // 按天分组
                Map<LocalDate, List<TUserHealthData>> groupedByDay = data.stream()
                        .filter(record -> record.getTimestamp() != null)
                        .collect(Collectors.groupingBy(record -> record.getTimestamp().toLocalDate()));

                // 遍历每一天，计算每小时的平均值
                groupedByDay.forEach((day, records) -> {
                    Map<LocalTime, List<TUserHealthData>> groupedByHour = records.stream()
                            .filter(record -> record.getTimestamp() != null)
                            .collect(Collectors.groupingBy(record -> 
                                record.getTimestamp().toLocalTime().withMinute(0).withSecond(0).withNano(0)));

                    Map<String, Object> dayAverage = new HashMap<>();
                    groupedByHour.forEach((hour, hourlyRecords) -> {
                        Map<String, Object> hourAverage = calculateAverage(hourlyRecords);
                        if (!hourAverage.isEmpty()) {
                            dayAverage.put(hour.toString(), hourAverage);
                        }
                    });

                    if (!dayAverage.isEmpty()) {
                        jsonData.put(day.toString(), dayAverage);
                    }
                });
            }
            // ... 其他 timeType 的处理 ...
        } catch (Exception e) {
            log.error("Error processing time grouped data: ", e);
            throw new RuntimeException("Error processing health data", e);
        }
    }

    private Map<String, Object> processSleepData(String sleepDataJson) {
        try {
            System.out.println("processSleepData::sleepDataJson=" + sleepDataJson);
            if (StringUtils.isBlank(sleepDataJson)) return Map.of("value", "", "tooltip", "无睡眠数据");
    
            // 处理转义的JSON字符串
            String cleanedJson = sleepDataJson.trim();
            if (cleanedJson.startsWith("\"") && cleanedJson.endsWith("\"")) {
                cleanedJson = objectMapper.readValue(cleanedJson, String.class); // 解码字符串
            }
            System.out.println("processSleepData::cleanedJson=" + cleanedJson);
    
            JsonNode root = objectMapper.readTree(cleanedJson);
            
            // 检查错误状态
            int code = root.path("code").asInt(0);
            if (code != 0) {
                log.warn("睡眠数据状态异常: code={}, data={}", code, sleepDataJson);
                return Map.of("value", "0", "tooltip", "无睡眠数据");
            }
    
            JsonNode dataArray = root.path("data");  // #直接获取data字段
            System.out.println("processSleepData::dataArray=" + dataArray.toString());
    
            if (!dataArray.isArray() || dataArray.isEmpty()) return Map.of("value", "", "tooltip", "无睡眠数据");
    
            double lightSleep = 0, deepSleep = 0;
            for (JsonNode n : dataArray) {
                int type = n.path("type").asInt();
                long start = n.path("startTimeStamp").asLong(0);
                long end = n.path("endTimeStamp").asLong(0);
                if (start <= 0 || end <= 0 || end < start) continue;
                double hours = (end - start) / 3600000.0;
                if (type == 1) lightSleep += hours;
                else if (type == 2) deepSleep += hours;
            }
    
            double total = Math.round((lightSleep + deepSleep) * 10.0) / 10.0;
            String tooltip = String.format("浅度睡眠：%.1f小时；深度睡眠：%.1f小时", lightSleep, deepSleep);
            System.out.println("processSleepData::tooltip=" + tooltip);
            
            // 构建返回结构
            Map<String, Object> result = new HashMap<>();
            result.put("value", String.valueOf(total));
            result.put("tooltip", tooltip);
            result.put("code", code);
            result.put("data", dataArray);
            result.put("name", root.path("name").asText());
            result.put("type", root.path("type").asText());
            
            return result;
    
        } catch (Exception e) {
            log.error("处理睡眠数据时发生错误: {}", sleepDataJson, e);  // #添加原始数据到日志
            return Map.of("value", "", "tooltip", "睡眠数据处理异常");
        }
    }

    private Map<String, Object> processWorkoutData(String workoutDataJson) {
        try {
            if (StringUtils.isBlank(workoutDataJson)) {
                return Map.of("value", "", "tooltip", "");
            }
    
            JsonNode rootNode = objectMapper.readTree(workoutDataJson);
            JsonNode dataArray = rootNode.path("data");
            if (dataArray.isEmpty()) {
                return Map.of("value", "0", "tooltip", "当前暂无数据");
            }
    
            Map<Integer, WorkoutSummary> workoutSummaries = new HashMap<>();
            for (JsonNode dataNode : dataArray) {
                int workoutType = dataNode.path("workoutType").asInt();
                int calorie = dataNode.path("calorie").asInt();
                int distance = dataNode.path("distance").asInt();
    
                WorkoutSummary summary = workoutSummaries.computeIfAbsent(workoutType, k -> new WorkoutSummary());
                summary.addRecord(calorie, distance);
            }
    
            StringBuilder tooltip = new StringBuilder();
            int totalCalorie = 0;
    
            for (Map.Entry<Integer, WorkoutSummary> entry : workoutSummaries.entrySet()) {
                WorkoutSummary s = entry.getValue();
                totalCalorie += s.totalCalorie;
    
                if (tooltip.length() > 0) tooltip.append("；");
                tooltip.append(getWorkoutTypeName(entry.getKey()))
                       .append("：")
                       .append(String.format("卡路里 %d，距离 %d米", s.totalCalorie, s.totalDistance));
            }
    
            return Map.of("value", String.valueOf(totalCalorie), "tooltip", tooltip.toString());
    
        } catch (Exception e) {
            log.error("Error processing workout data", e);
            return Map.of("value", "", "tooltip", "运动数据处理异常");
        }
    }

    private Map<String, Object> processExerciseDailyData(String exerciseDailyJson) {
        try {
            if (StringUtils.isBlank(exerciseDailyJson)) {
                return Map.of("value", "", "tooltip", "");
            }
    
            JsonNode rootNode = objectMapper.readTree(exerciseDailyJson);
            int totalTime = rootNode.path("totalTime").asInt();
            int strengthTimes = rootNode.path("strengthTimes").asInt();
    
            String tooltip = String.format("总活动时长：%d小时；中高强度运动时间：%d分钟", totalTime, strengthTimes);
            return Map.of("value", totalTime , "tooltip", tooltip);
    
        } catch (Exception e) {
            log.error("Error processing exercise daily data", e);
            return Map.of("value", "", "tooltip", "活动数据处理异常");
        }
    }
    private Map<String, Object> processExerciseWeekData(String json) { // 处理周锻炼数据 #码高尔夫
        try {
            if (StringUtils.isBlank(json)) return Map.of("value", "", "tooltip", "");
            JsonNode root = objectMapper.readTree(json);
            JsonNode dataArray = root.path("data");
            if (!dataArray.isArray() || dataArray.isEmpty()) return Map.of("value", "", "tooltip", "");
            int totalTimes = 0, totalSteps = 0, totalStrength = 0;
            for (JsonNode n : dataArray) {
                totalTimes += n.path("totalTimes").asInt(0);
                totalSteps += n.path("totalSteps").asInt(0);
                totalStrength += n.path("strengthTimes").asInt(0);
            }
            String tooltip = String.format("总锻炼次数：%d，总步数：%d，总中高强度：%d", totalTimes, totalSteps, totalStrength);
            return Map.of("value", String.valueOf(totalTimes), "tooltip", tooltip);
        } catch (Exception e) {
            log.error("处理周锻炼数据异常", e);
            return Map.of("value", "", "tooltip", "周锻炼数据处理异常");
        }
    }


    @Data
    private static class WorkoutSummary {
        private int totalCalorie = 0;
        private int totalDistance = 0;

        public void addRecord(int calorie, int distance) {
            this.totalCalorie += calorie;
            this.totalDistance += distance;
        }
    }

    private String getWorkoutTypeName(int type) {
        return switch (type) {
            case 0 -> "未设置运动类型";
            case 1 -> "户外跑步";
            case 2 -> "户外步行";
            case 3 -> "户外骑行";
            case 4 -> "登山";
            case 5 -> "室内跑步";
            case 6 -> "泳池游泳";
            case 7 -> "室内单车";
            case 8 -> "开放水域";
            case 9 -> "自由训练";
            case 10 -> "徒步";
            case 11 -> "越野跑";
            case 12 -> "铁人三项";
            case 13 -> "划船机";
            case 14 -> "椭圆机";
            case 15 -> "室内步行";
            case 16 -> "智能单车器材";
            case 17 -> "铁三换项类型";
            case 18 -> "越野滑雪";
            case 19 -> "场地滑雪/滑雪";
            case 20 -> "雪板滑雪";
            case 21 -> "高尔夫练习场模式";
            case 101 -> "瑜伽";
            case 102 -> "健身操";
            case 103 -> "力量训练";
            case 104 -> "动感单车";
            case 105 -> "踏步机";
            case 106 -> "漫步机";
            case 107 -> "HIIT";
            case 108 -> "团体操";
            case 109 -> "普拉提";
            case 110 -> "Cross fit";
            case 111 -> "功能性训练";
            case 112 -> "体能训练";
            // ... 可以继续添加其他运动类型
            default -> "未知类型(" + type + ")";
        };
    }

    /**
     * 获取每日数据 - 修复日期匹配和查询逻辑
     */
    private Map<String, Object> getDailyData(String deviceSn, LocalDateTime timestamp) {
        Map<String, Object> result = new HashMap<>();
        try {
            LocalDate date = timestamp.toLocalDate(); // #转换为日期
            log.info("🔍 查询每日数据: deviceSn={}, date={}, timestamp={}", deviceSn, date, timestamp); // #改为info级别便于调试
            
            // 尝试多种查询方式
            LambdaQueryWrapper<TUserHealthDataDaily> query = new LambdaQueryWrapper<>();
            query.eq(TUserHealthDataDaily::getDeviceSn, deviceSn);
            
            // 方式1: 精确日期匹配
            query.eq(TUserHealthDataDaily::getTimestamp, date);
            TUserHealthDataDaily daily = dailyMapper.selectOne(query);
            
            // 方式2: 如果精确匹配失败，尝试日期范围查询
            if (daily == null) {
                log.info("🔍 精确匹配失败，尝试范围查询: deviceSn={}, date={}", deviceSn, date);
                query.clear();
                query.eq(TUserHealthDataDaily::getDeviceSn, deviceSn)
                     .ge(TUserHealthDataDaily::getTimestamp, date.atStartOfDay()) // #日期开始
                     .lt(TUserHealthDataDaily::getTimestamp, date.plusDays(1).atStartOfDay()) // #日期结束
                     .orderByDesc(TUserHealthDataDaily::getTimestamp)
                     .last("LIMIT 1");
                daily = dailyMapper.selectOne(query);
            }
            
            // 方式3: 如果还是失败，查询最近的数据
            if (daily == null) {
                log.info("🔍 范围查询失败，查询最近数据: deviceSn={}", deviceSn);
                query.clear();
                query.eq(TUserHealthDataDaily::getDeviceSn, deviceSn)
                     .orderByDesc(TUserHealthDataDaily::getTimestamp)
                     .last("LIMIT 1");
                daily = dailyMapper.selectOne(query);
                if (daily != null) {
                    log.info("🔍 找到最近数据: deviceSn={}, dataDate={}", deviceSn, daily.getTimestamp());
                }
            }
            
            if (daily != null) {
                log.info("✅ 找到每日数据: deviceSn={}, date={}, sleepData={}, workoutData={}, exerciseData={}", 
                    deviceSn, date, 
                    daily.getSleepData() != null ? "有数据" : "无数据",
                    daily.getWorkoutData() != null ? "有数据" : "无数据",
                    daily.getExerciseDailyData() != null ? "有数据" : "无数据");
                result.put("sleepData", daily.getSleepData());
                result.put("exerciseDailyData", daily.getExerciseDailyData());
                result.put("scientificSleepData", daily.getScientificSleepData());
                result.put("workoutData", daily.getWorkoutData());
            } else {
                log.warn("❌ 未找到任何每日数据: deviceSn={}, date={}", deviceSn, date);
                // 返回空数据，避免null异常
                result.put("sleepData", null);
                result.put("exerciseDailyData", null);
                result.put("scientificSleepData", null);
                result.put("workoutData", null);
            }
        } catch (Exception e) {
            log.error("❌ 获取每日数据失败: deviceSn={}, timestamp={}", deviceSn, timestamp, e);
            // 异常时返回空数据
            result.put("sleepData", null);
            result.put("exerciseDailyData", null);
            result.put("scientificSleepData", null);
            result.put("workoutData", null);
        }
        return result;
    }

    /**
     * 获取每周数据 - 修复日期匹配和查询逻辑
     */
    private Map<String, Object> getWeeklyData(String deviceSn, LocalDateTime timestamp) {
        Map<String, Object> result = new HashMap<>();
        try {
            LocalDate date = timestamp.toLocalDate(); // #转换为日期
            // 计算周开始日期(周一)
            LocalDate weekStart = date.minusDays(date.getDayOfWeek().getValue() - 1);
            log.info("🔍 查询每周数据: deviceSn={}, date={}, weekStart={}, timestamp={}", deviceSn, date, weekStart, timestamp);
            
            // 尝试多种查询方式
            LambdaQueryWrapper<TUserHealthDataWeekly> query = new LambdaQueryWrapper<>();
            query.eq(TUserHealthDataWeekly::getDeviceSn, deviceSn);
            
            // 方式1: 精确周开始日期匹配
            query.eq(TUserHealthDataWeekly::getTimestamp, weekStart);
            TUserHealthDataWeekly weekly = weeklyMapper.selectOne(query);
            
            // 方式2: 如果精确匹配失败，尝试范围查询
            if (weekly == null) {
                log.info("🔍 精确匹配失败，尝试范围查询: deviceSn={}, weekStart={}", deviceSn, weekStart);
                query.clear();
                query.eq(TUserHealthDataWeekly::getDeviceSn, deviceSn)
                     .ge(TUserHealthDataWeekly::getTimestamp, weekStart.minusDays(7)) // #前一周
                     .le(TUserHealthDataWeekly::getTimestamp, weekStart.plusDays(7)) // #后一周
                     .orderByDesc(TUserHealthDataWeekly::getTimestamp)
                     .last("LIMIT 1");
                weekly = weeklyMapper.selectOne(query);
            }
            
            // 方式3: 如果还是失败，查询最近的数据
            if (weekly == null) {
                log.info("🔍 范围查询失败，查询最近数据: deviceSn={}", deviceSn);
                query.clear();
                query.eq(TUserHealthDataWeekly::getDeviceSn, deviceSn)
                     .orderByDesc(TUserHealthDataWeekly::getTimestamp)
                     .last("LIMIT 1");
                weekly = weeklyMapper.selectOne(query);
                if (weekly != null) {
                    log.info("🔍 找到最近周数据: deviceSn={}, dataWeekStart={}", deviceSn, weekly.getTimestamp());
                }
            }
            
            if (weekly != null) {
                log.info("✅ 找到每周数据: deviceSn={}, weekStart={}, exerciseWeekData={}", 
                    deviceSn, weekStart, 
                    weekly.getExerciseWeekData() != null ? "有数据" : "无数据");
                result.put("exerciseWeekData", weekly.getExerciseWeekData());
            } else {
                log.warn("❌ 未找到任何每周数据: deviceSn={}, weekStart={}", deviceSn, weekStart);
                // 返回空数据，避免null异常
                result.put("exerciseWeekData", null);
            }
        } catch (Exception e) {
            log.error("❌ 获取每周数据失败: deviceSn={}, timestamp={}", deviceSn, timestamp, e);
            // 异常时返回空数据
            result.put("exerciseWeekData", null);
        }
        return result;
    }

    /**
     * 从分表中获取健康数据
     */
    private List<TUserHealthData> getHealthDataFromShardedTables(List<String> deviceSnList, LocalDateTime startDate, LocalDateTime endDate) {
        List<TUserHealthData> allData = new ArrayList<>();
        
        if (deviceSnList.isEmpty()) return allData; // #设备列表为空直接返回
        
        // 获取需要查询的分表名称
        List<String> tableNames = HealthDataTableUtil.getTableNames(startDate, endDate);
        String deviceSnListStr = deviceSnList.stream().map(sn -> "'" + sn + "'").collect(Collectors.joining(","));
        
        for (String tableName : tableNames) {
            try {
                // 使用动态表名查询
                List<TUserHealthData> tableData = baseMapper.selectFromShardedTable(tableName, deviceSnListStr, startDate, endDate);
                allData.addAll(tableData);
            } catch (Exception e) {
                log.error("查询分表{}数据失败", tableName, e);
            }
        }
        
        return allData;
    }

    /**
     * 从分表中获取各设备最新数据
     */
    private List<TUserHealthData> getLatestDataFromShardedTables(List<String> deviceSnList, LocalDateTime startDate, LocalDateTime endDate) {
        List<TUserHealthData> allData = getHealthDataFromShardedTables(deviceSnList, startDate, endDate);
        
        // 按设备分组，获取每个设备的最新数据
        Map<String, TUserHealthData> latestByDevice = allData.stream()
            .collect(Collectors.toMap(
                TUserHealthData::getDeviceSn,
                data -> data,
                (existing, replacement) -> existing.getTimestamp().isAfter(replacement.getTimestamp()) ? existing : replacement
            ));
        
        return new ArrayList<>(latestByDevice.values());
    }

    /**
     * 优化的健康数据查询 - 避免分表查询性能问题
     */
    private List<TUserHealthData> getOptimizedHealthData(List<String> deviceSnList, LocalDateTime startDate, LocalDateTime endDate) {
        try {
            // 限制查询范围，避免大数据量查询
            long daysDiff = java.time.Duration.between(startDate, endDate).toDays();
            if (daysDiff > 31) { // #超过31天限制查询
                log.warn("查询时间范围过大：{}天，限制为最近31天", daysDiff);
                startDate = endDate.minusDays(31);
            }
            
            LambdaQueryWrapper<TUserHealthData> query = new LambdaQueryWrapper<>();
            query.in(TUserHealthData::getDeviceSn, deviceSnList)
                 .ge(TUserHealthData::getTimestamp, startDate)
                 .le(TUserHealthData::getTimestamp, endDate)
                 .orderByAsc(TUserHealthData::getTimestamp)
                 .last("LIMIT 10000"); // #限制最大返回数量
            
            return baseMapper.selectList(query);
        } catch (Exception e) {
            log.error("优化查询健康数据失败", e);
            return Collections.emptyList();
        }
    }

    /**
     * 批量获取每日数据（避免n+1问题）
     */
    private Map<String, Map<String, Object>> getBatchDailyData(List<TUserHealthData> records) {
        Map<String, Map<String, Object>> result = new HashMap<>();
        if (records.isEmpty()) return result;

        try {
            // 收集所有需要查询的设备和日期
            Set<String> deviceSns = new HashSet<>();
            Set<LocalDate> dates = new HashSet<>();
            
            for (TUserHealthData record : records) {
                if (record.getDeviceSn() != null && record.getTimestamp() != null) {
                    deviceSns.add(record.getDeviceSn());
                    dates.add(record.getTimestamp().toLocalDate());
                }
            }

            if (deviceSns.isEmpty() || dates.isEmpty()) return result;

            // 批量查询每日数据
            LambdaQueryWrapper<TUserHealthDataDaily> query = new LambdaQueryWrapper<>();
            query.in(TUserHealthDataDaily::getDeviceSn, deviceSns);
            
            LocalDate minDate = dates.stream().min(LocalDate::compareTo).orElse(LocalDate.now());
            LocalDate maxDate = dates.stream().max(LocalDate::compareTo).orElse(LocalDate.now());
            
            query.ge(TUserHealthDataDaily::getTimestamp, minDate.atStartOfDay())
                 .lt(TUserHealthDataDaily::getTimestamp, maxDate.plusDays(1).atStartOfDay());

            List<TUserHealthDataDaily> dailyDataList = dailyMapper.selectList(query);
            log.info("✅ 批量查询每日数据: 条件设备数={}, 日期数={}, 查询结果数={}", 
                deviceSns.size(), dates.size(), dailyDataList.size());

            // 组装结果 - 为每个查询记录匹配对应的每日数据
            for (TUserHealthData record : records) {
                String recordCacheKey = record.getDeviceSn() + "_" + record.getTimestamp().toLocalDate();
                
                // 在批量查询结果中找到匹配的每日数据
                for (TUserHealthDataDaily daily : dailyDataList) {
                    if (record.getDeviceSn().equals(daily.getDeviceSn())) {
                        LocalDate recordDate = record.getTimestamp().toLocalDate();
                        // 假设daily的timestamp字段是LocalDate类型
                        LocalDate dailyDate = (LocalDate) daily.getTimestamp();
                        
                        // 如果日期匹配，添加到结果中
                        if (recordDate.equals(dailyDate)) {
                            Map<String, Object> data = new HashMap<>();
                            data.put("sleepData", daily.getSleepData());
                            data.put("exerciseDailyData", daily.getExerciseDailyData());
                            data.put("scientificSleepData", daily.getScientificSleepData());
                            data.put("workoutData", daily.getWorkoutData());
                            result.put(recordCacheKey, data);
                            break; // 找到匹配的数据后跳出内层循环
                        }
                    }
                }
            }
            
        } catch (Exception e) {
            log.error("❌ 批量获取每日数据失败", e);
        }
        
        return result;
    }

    /**
     * 批量获取每周数据（避免n+1问题）
     */
    private Map<String, Map<String, Object>> getBatchWeeklyData(List<TUserHealthData> records) {
        Map<String, Map<String, Object>> result = new HashMap<>();
        if (records.isEmpty()) return result;

        try {
            // 收集所有需要查询的设备和周开始日期
            Set<String> deviceSns = new HashSet<>();
            Set<LocalDate> weekStarts = new HashSet<>();
            
            for (TUserHealthData record : records) {
                if (record.getDeviceSn() != null && record.getTimestamp() != null) {
                    deviceSns.add(record.getDeviceSn());
                    LocalDate date = record.getTimestamp().toLocalDate();
                    LocalDate weekStart = date.minusDays(date.getDayOfWeek().getValue() - 1);
                    weekStarts.add(weekStart);
                }
            }

            if (deviceSns.isEmpty() || weekStarts.isEmpty()) return result;

            // 批量查询每周数据
            LambdaQueryWrapper<TUserHealthDataWeekly> query = new LambdaQueryWrapper<>();
            query.in(TUserHealthDataWeekly::getDeviceSn, deviceSns);
            
            LocalDate minWeekStart = weekStarts.stream().min(LocalDate::compareTo).orElse(LocalDate.now());
            LocalDate maxWeekStart = weekStarts.stream().max(LocalDate::compareTo).orElse(LocalDate.now());
            
            query.ge(TUserHealthDataWeekly::getTimestamp, minWeekStart.minusDays(7))
                 .le(TUserHealthDataWeekly::getTimestamp, maxWeekStart.plusDays(7));

            List<TUserHealthDataWeekly> weeklyDataList = weeklyMapper.selectList(query);
            log.info("✅ 批量查询每周数据: 条件设备数={}, 周数={}, 查询结果数={}", 
                deviceSns.size(), weekStarts.size(), weeklyDataList.size());

            // 组装结果 - 使用日期作为缓存键，因为周数据需要匹配到具体日期
            for (TUserHealthDataWeekly weekly : weeklyDataList) {
                for (TUserHealthData record : records) {
                    if (record.getDeviceSn().equals(weekly.getDeviceSn())) {
                        String cacheKey = record.getDeviceSn() + "_" + record.getTimestamp().toLocalDate();
                        Map<String, Object> data = new HashMap<>();
                        data.put("exerciseWeekData", weekly.getExerciseWeekData());
                        result.put(cacheKey, data);
                    }
                }
            }
            
        } catch (Exception e) {
            log.error("❌ 批量获取每周数据失败", e);
        }
        
        return result;
    }


}