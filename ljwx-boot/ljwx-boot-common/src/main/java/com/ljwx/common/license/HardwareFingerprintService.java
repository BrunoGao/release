package com.ljwx.common.license;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.net.NetworkInterface;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 硬件指纹服务
 * 生成基于硬件信息的唯一标识，用于许可证绑定
 */
@Slf4j
@Service
public class HardwareFingerprintService {
    
    /**
     * 生成硬件指纹
     */
    public String generateFingerprint() {
        try {
            Map<String, String> hwInfo = new HashMap<>();
            
            // 1. CPU信息
            String cpuInfo = getCpuInfo();
            hwInfo.put("cpu", cpuInfo);
            
            // 2. 主板信息
            String boardInfo = getBoardInfo();
            hwInfo.put("board", boardInfo);
            
            // 3. 网络MAC地址
            String macAddress = getMacAddress();
            hwInfo.put("mac", macAddress);
            
            // 4. 系统信息
            String systemInfo = getSystemInfo();
            hwInfo.put("system", systemInfo);
            
            // 5. 磁盘信息
            String diskInfo = getDiskInfo();
            hwInfo.put("disk", diskInfo);
            
            // 6. 组合并生成指纹
            String combined = hwInfo.entrySet().stream()
                .filter(entry -> entry.getValue() != null && !entry.getValue().isEmpty())
                .sorted(Map.Entry.comparingByKey())
                .map(entry -> entry.getKey() + "=" + entry.getValue())
                .collect(Collectors.joining("|"));
            
            String fingerprint = sha256Hash(combined);
            
            log.debug("硬件指纹组合信息: {}", combined);
            log.info("生成硬件指纹: {}", fingerprint);
            
            return fingerprint;
            
        } catch (Exception e) {
            log.error("生成硬件指纹失败", e);
            return "FALLBACK_" + System.currentTimeMillis();
        }
    }
    
    /**
     * 获取CPU信息
     */
    private String getCpuInfo() {
        try {
            // Linux系统读取/proc/cpuinfo
            if (isLinux()) {
                String cpuinfo = readFile("/proc/cpuinfo");
                if (cpuinfo != null) {
                    // 提取CPU型号和序列号
                    return extractValue(cpuinfo, "model name") + "_" + 
                           extractValue(cpuinfo, "processor");
                }
            }
            
            // Windows系统使用系统属性
            String arch = System.getProperty("os.arch");
            String processors = String.valueOf(Runtime.getRuntime().availableProcessors());
            return arch + "_" + processors;
            
        } catch (Exception e) {
            log.warn("获取CPU信息失败", e);
            return System.getProperty("os.arch", "unknown");
        }
    }
    
    /**
     * 获取主板信息
     */
    private String getBoardInfo() {
        try {
            if (isLinux()) {
                // 尝试读取DMI信息
                String boardSerial = readFile("/sys/class/dmi/id/board_serial");
                String boardVendor = readFile("/sys/class/dmi/id/board_vendor");
                String boardName = readFile("/sys/class/dmi/id/board_name");
                
                if (boardSerial != null && !boardSerial.trim().isEmpty()) {
                    return boardVendor + "_" + boardName + "_" + boardSerial;
                }
            }
            
            // 备用方案：使用系统属性
            return System.getProperty("os.name") + "_" + System.getProperty("os.version");
            
        } catch (Exception e) {
            log.warn("获取主板信息失败", e);
            return System.getProperty("os.name", "unknown");
        }
    }
    
    /**
     * 获取MAC地址
     */
    private String getMacAddress() {
        try {
            StringBuilder macAddresses = new StringBuilder();
            Enumeration<NetworkInterface> networkInterfaces = NetworkInterface.getNetworkInterfaces();
            
            while (networkInterfaces.hasMoreElements()) {
                NetworkInterface ni = networkInterfaces.nextElement();
                byte[] hardwareAddress = ni.getHardwareAddress();
                
                if (hardwareAddress != null && hardwareAddress.length > 0) {
                    StringBuilder mac = new StringBuilder();
                    for (byte b : hardwareAddress) {
                        mac.append(String.format("%02X", b));
                    }
                    
                    // 排除虚拟网卡
                    String macStr = mac.toString();
                    if (!isVirtualMac(macStr)) {
                        macAddresses.append(macStr).append(",");
                    }
                }
            }
            
            String result = macAddresses.toString();
            return result.endsWith(",") ? result.substring(0, result.length() - 1) : result;
            
        } catch (Exception e) {
            log.warn("获取MAC地址失败", e);
            return "unknown_mac";
        }
    }
    
    /**
     * 获取系统信息
     */
    private String getSystemInfo() {
        try {
            if (isLinux()) {
                String machineId = readFile("/etc/machine-id");
                if (machineId != null && !machineId.trim().isEmpty()) {
                    return machineId.trim();
                }
                
                String systemUuid = readFile("/sys/class/dmi/id/product_uuid");
                if (systemUuid != null && !systemUuid.trim().isEmpty()) {
                    return systemUuid.trim();
                }
            }
            
            // 备用方案
            return System.getProperty("user.name") + "_" + 
                   System.getProperty("java.version");
            
        } catch (Exception e) {
            log.warn("获取系统信息失败", e);
            return "unknown_system";
        }
    }
    
    /**
     * 获取磁盘信息
     */
    private String getDiskInfo() {
        try {
            File[] roots = File.listRoots();
            StringBuilder diskInfo = new StringBuilder();
            
            for (File root : roots) {
                long totalSpace = root.getTotalSpace();
                if (totalSpace > 0) {
                    diskInfo.append(root.getAbsolutePath())
                           .append(":")
                           .append(totalSpace)
                           .append(",");
                }
            }
            
            String result = diskInfo.toString();
            return result.endsWith(",") ? result.substring(0, result.length() - 1) : result;
            
        } catch (Exception e) {
            log.warn("获取磁盘信息失败", e);
            return "unknown_disk";
        }
    }
    
    /**
     * 读取文件内容
     */
    private String readFile(String filePath) {
        try {
            if (!Files.exists(Paths.get(filePath))) {
                return null;
            }
            
            return Files.readString(Paths.get(filePath)).trim();
            
        } catch (Exception e) {
            log.debug("读取文件失败: {}", filePath);
            return null;
        }
    }
    
    /**
     * 从文本中提取指定键的值
     */
    private String extractValue(String text, String key) {
        try {
            String[] lines = text.split("\\n");
            for (String line : lines) {
                if (line.startsWith(key + ":") || line.startsWith(key + "\\t")) {
                    String[] parts = line.split("[:;\\t]", 2);
                    if (parts.length > 1) {
                        return parts[1].trim();
                    }
                }
            }
        } catch (Exception e) {
            log.debug("提取值失败: key={}", key);
        }
        return "";
    }
    
    /**
     * 判断是否为Linux系统
     */
    private boolean isLinux() {
        return System.getProperty("os.name").toLowerCase().contains("linux");
    }
    
    /**
     * 判断是否为虚拟MAC地址
     */
    private boolean isVirtualMac(String mac) {
        // 常见虚拟网卡MAC地址前缀
        String[] virtualPrefixes = {
            "00505E", "000C29", "001C14", "005056", // VMware
            "080027", "0A0027",                     // VirtualBox  
            "001B21", "00155D",                     // Hyper-V
            "020000", "025041"                      // 其他虚拟化
        };
        
        for (String prefix : virtualPrefixes) {
            if (mac.startsWith(prefix)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * SHA256哈希
     */
    private String sha256Hash(String input) throws NoSuchAlgorithmException {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(input.getBytes());
        
        StringBuilder hexString = new StringBuilder();
        for (byte b : hash) {
            String hex = Integer.toHexString(0xff & b);
            if (hex.length() == 1) {
                hexString.append('0');
            }
            hexString.append(hex);
        }
        
        return hexString.toString().toUpperCase();
    }
    
    /**
     * 验证硬件指纹是否匹配
     */
    public boolean verifyFingerprint(String expectedFingerprint) {
        try {
            String currentFingerprint = generateFingerprint();
            boolean matches = currentFingerprint.equals(expectedFingerprint);
            
            if (!matches) {
                log.warn("硬件指纹验证失败:");
                log.warn("  期望值: {}", expectedFingerprint);
                log.warn("  实际值: {}", currentFingerprint);
            } else {
                log.info("硬件指纹验证成功");
            }
            
            return matches;
            
        } catch (Exception e) {
            log.error("硬件指纹验证过程失败", e);
            return false;
        }
    }
    
    /**
     * 生成硬件信息报告
     */
    public Map<String, String> generateHardwareReport() {
        Map<String, String> report = new HashMap<>();
        
        report.put("cpu_info", getCpuInfo());
        report.put("board_info", getBoardInfo());
        report.put("mac_address", getMacAddress());
        report.put("system_info", getSystemInfo());
        report.put("disk_info", getDiskInfo());
        report.put("fingerprint", generateFingerprint());
        report.put("os_name", System.getProperty("os.name"));
        report.put("os_version", System.getProperty("os.version"));
        report.put("java_version", System.getProperty("java.version"));
        report.put("generated_time", new Date().toString());
        
        return report;
    }
}