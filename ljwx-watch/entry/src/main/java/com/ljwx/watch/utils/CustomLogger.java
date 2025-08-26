package com.ljwx.watch.utils;

import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import org.json.JSONObject;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 自定义日志工具类，支持中文字符和完整数据打印
 * 解决HiLog数据截断问题
 * 主要功能：
 * 1. 通过HiLog分段输出完整数据，避免截断
 * 2. 支持中文字符输出
 * 3. 专门的健康数据、设备数据、通用事件日志方法
 */
public class CustomLogger {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "ljwx");
    
    public enum LogLevel {
        DEBUG, INFO, WARN, ERROR
    }
    
    /**
     * 打印信息级别日志，同时输出到HiLog和文件
     */
    public static void info(String tag, String message) {
        log(LogLevel.INFO, tag, message);
    }
    
    /**
     * 打印警告级别日志，同时输出到HiLog和文件  
     */
    public static void warn(String tag, String message) {
        log(LogLevel.WARN, tag, message);
    }
    
    /**
     * 打印错误级别日志，同时输出到HiLog和文件
     */
    public static void error(String tag, String message) {
        log(LogLevel.ERROR, tag, message);
    }
    
    /**
     * 打印调试级别日志，同时输出到HiLog和文件
     */
    public static void debug(String tag, String message) {
        log(LogLevel.DEBUG, tag, message);
    }
    
    /**
     * 核心日志打印方法
     */
    private static void log(LogLevel level, String tag, String message) {
        // 输出到HiLog（支持中英文混合）
        switch (level) {
            case DEBUG:
                HiLog.debug(LABEL_LOG, tag + ": " + message);
                break;
            case INFO:
                HiLog.info(LABEL_LOG, tag + ": " + message);
                break;
            case WARN:
                HiLog.warn(LABEL_LOG, tag + ": " + message);
                break;
            case ERROR:
                HiLog.error(LABEL_LOG, tag + ": " + message);
                break;
        }
        
        // 同时打印到System.out确保可见
        System.out.println(tag + ": " + message);
    }
    
    /**
     * 专门用于分段打印长数据的方法，避免HiLog截断
     */
    public static void logLongData(String tag, String title, String data) {
        info(tag, "=== " + title + " 开始 ===");
        
        if (data == null || data.isEmpty()) {
            warn(tag, title + " 数据为空");
            return;
        }
        
        // 分段打印数据，每段500字符
        final int chunkSize = 500;
        int totalLength = data.length();
        int chunkCount = (totalLength + chunkSize - 1) / chunkSize;
        
        info(tag, String.format("%s 数据总长度: %d 字符，分 %d 段输出", title, totalLength, chunkCount));
        
        for (int i = 0; i < chunkCount; i++) {
            int start = i * chunkSize;
            int end = Math.min(start + chunkSize, totalLength);
            String chunk = data.substring(start, end);
            
            info(tag, String.format("%s 第%d/%d段: %s", title, i + 1, chunkCount, chunk));
        }
        
        info(tag, "=== " + title + " 结束 ===");
    }
    
    /**
     * 专门用于打印健康信息的方法
     */
    public static void logHealthInfo(String scenario, String healthData) {
        String tag = "HealthInfo";
        info(tag, "=== " + scenario + " 健康信息详情 ===");
        
        try {
            if (healthData != null && !healthData.isEmpty()) {
                JSONObject json = new JSONObject(healthData);
                if (json.has("data")) {
                    JSONObject data = json.getJSONObject("data");
                    
                    info(tag, String.format("设备序列号: %s", data.optString("deviceSn", "未知")));
                    info(tag, String.format("心率: %d bpm", data.optInt("heart_rate", 0)));
                    info(tag, String.format("血氧: %d%%", data.optInt("blood_oxygen", 0)));
                    info(tag, String.format("体温: %s°C", data.optString("body_temperature", "0.0")));
                    info(tag, String.format("收缩压: %d mmHg", data.optInt("blood_pressure_systolic", 0)));
                    info(tag, String.format("舒张压: %d mmHg", data.optInt("blood_pressure_diastolic", 0)));
                    info(tag, String.format("步数: %d步", data.optInt("step", 0)));
                    info(tag, String.format("距离: %s公里", data.optString("distance", "0.0")));
                    info(tag, String.format("卡路里: %s千卡", data.optString("calorie", "0.0")));
                    info(tag, String.format("压力指数: %d", data.optInt("stress", 0)));
                    info(tag, String.format("上传方式: %s", data.optString("upload_method", "wifi")));
                    info(tag, String.format("时间戳: %s", data.optString("timestamp", "未知")));
                    info(tag, String.format("位置信息: 纬度=%s, 经度=%s, 海拔=%s", 
                        data.optString("latitude", "0"), 
                        data.optString("longitude", "0"), 
                        data.optString("altitude", "0")));
                }
                
                // 使用分段日志方法确保完整JSON通过HiLog输出
                logLongData(tag, scenario + " 完整健康数据JSON", json.toString(2));
            } else {
                warn(tag, scenario + " 健康数据为空或null");
            }
        } catch (Exception e) {
            error(tag, "解析健康数据时发生错误: " + e.getMessage());
            logLongData(tag, scenario + " 原始健康数据(解析失败)", healthData != null ? healthData : "null");
        }
        
        info(tag, "=== " + scenario + " 健康信息结束 ===");
    }
    
    /**
     * 专门用于打印设备信息的方法  
     */
    public static void logDeviceInfo(String scenario, String deviceData) {
        String tag = "DeviceInfo";
        info(tag, "=== " + scenario + " 设备信息详情 ===");
        
        try {
            if (deviceData != null && !deviceData.isEmpty()) {
                JSONObject json = new JSONObject(deviceData);
                
                info(tag, String.format("设备序列号: %s", json.optString("SerialNumber", "未知")));
                info(tag, String.format("设备型号: %s", json.optString("Product Model", "未知")));
                info(tag, String.format("硬件版本: %s", json.optString("Hardware Version", "未知")));
                info(tag, String.format("软件版本: %s", json.optString("Software Version", "未知")));
                info(tag, String.format("IP地址: %s", json.optString("IP Address", "未知")));
                info(tag, String.format("MAC地址: %s", json.optString("MAC", "未知")));
                info(tag, String.format("电池电量: %d%%", json.optInt("batteryLevel", 0)));
                info(tag, String.format("电池电压: %d mV", json.optInt("voltage", 0)));
                info(tag, String.format("充电状态: %s", getChargingStatusText(json.optInt("chargingStatus", 0))));
                info(tag, String.format("佩戴状态: %s", getWearStateText(json.optInt("wearState", 0))));
                info(tag, String.format("设备状态: %s", json.optString("status", "未知")));
                info(tag, String.format("时间戳: %s", json.optString("timestamp", "未知")));
                
                // 使用分段日志方法确保完整JSON通过HiLog输出
                logLongData(tag, scenario + " 完整设备信息JSON", json.toString(2));
            } else {
                warn(tag, scenario + " 设备数据为空或null");
            }
        } catch (Exception e) {
            error(tag, "解析设备数据时发生错误: " + e.getMessage());
            logLongData(tag, scenario + " 原始设备数据(解析失败)", deviceData != null ? deviceData : "null");
        }
        
        info(tag, "=== " + scenario + " 设备信息结束 ===");
    }
    
    /**
     * 专门用于打印通用事件的方法
     */
    public static void logCommonEvent(String scenario, String deviceInfo, String healthInfo) {
        String tag = "CommonEvent";
        info(tag, "=== " + scenario + " 通用事件详情 ===");
        
        info(tag, "包含数据类型: " + (deviceInfo != null ? "设备信息 " : "") + 
                  (healthInfo != null ? "健康信息" : ""));
        
        if (deviceInfo != null) {
            info(tag, "--- 通用事件中的设备信息 ---");
            logDeviceInfo("通用事件", deviceInfo);
            // 同时分段打印完整设备信息
            logLongData(tag, scenario + " 设备信息部分", deviceInfo);
        }
        
        if (healthInfo != null) {
            info(tag, "--- 通用事件中的健康信息 ---");
            logHealthInfo("通用事件", healthInfo);
            // 同时分段打印完整健康信息
            logLongData(tag, scenario + " 健康信息部分", healthInfo);
        }
        
        // 组合完整通用事件结构写入文件
        StringBuilder combinedEvent = new StringBuilder();
        combinedEvent.append("{\n");
        combinedEvent.append("  \"scenario\": \"").append(scenario).append("\",\n");
        if (deviceInfo != null) {
            combinedEvent.append("  \"deviceInfo\": ").append(deviceInfo).append(",\n");
        }
        if (healthInfo != null) {
            combinedEvent.append("  \"healthInfo\": ").append(healthInfo).append("\n");
        }
        combinedEvent.append("}");
        
        logLongData(tag, scenario + " 完整通用事件结构", combinedEvent.toString());
        
        info(tag, "=== " + scenario + " 通用事件结束 ===");
    }
    
    
    /**
     * 获取充电状态文本描述
     */
    private static String getChargingStatusText(int status) {
        switch (status) {
            case 1: return "充电中";
            case 2: return "放电中"; 
            case 3: return "未充电";
            case 4: return "充满";
            default: return "未知(" + status + ")";
        }
    }
    
    /**
     * 获取佩戴状态文本描述
     */
    private static String getWearStateText(int state) {
        switch (state) {
            case 0: return "未佩戴";
            case 1: return "已佩戴";
            default: return "未知(" + state + ")";
        }
    }
    
}