import java.io.*;
import java.net.NetworkInterface;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;
import java.util.Base64;

/**
 * 简单的许可证生成器
 * 用于为灵境万象健康管理系统生成开发用许可证
 */
public class LicenseGenerator {
    
    public static void main(String[] args) {
        try {
            LicenseGenerator generator = new LicenseGenerator();
            
            // 使用启动时检测到的实际硬件指纹
            String fingerprint = "96E2D4225BFDBAFA86A24D5608EBA3123CF714C58F82A2984256DEE6F7526CC2";
            System.out.println("使用硬件指纹: " + fingerprint);
            
            // 2. 生成许可证内容
            String licenseContent = generator.generateLicenseFile(fingerprint);
            
            // 3. 写入许可证文件
            Files.write(Paths.get("ljwx.lic"), licenseContent.getBytes());
            
            System.out.println("许可证文件已生成: ljwx.lic");
            System.out.println("许可证内容长度: " + licenseContent.length());
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    /**
     * 生成硬件指纹
     */
    public String generateFingerprint() {
        try {
            Map<String, String> hwInfo = new HashMap<>();
            
            // CPU信息
            String arch = System.getProperty("os.arch", "unknown");
            String processors = String.valueOf(Runtime.getRuntime().availableProcessors());
            hwInfo.put("cpu", arch + "_" + processors);
            
            // 系统信息
            String osName = System.getProperty("os.name", "unknown");
            String osVersion = System.getProperty("os.version", "unknown");
            hwInfo.put("system", osName + "_" + osVersion);
            
            // MAC地址
            String macAddress = getMacAddress();
            hwInfo.put("mac", macAddress);
            
            // 磁盘信息
            String diskInfo = getDiskInfo();
            hwInfo.put("disk", diskInfo);
            
            // 组合生成指纹
            String combined = hwInfo.entrySet().stream()
                .filter(entry -> entry.getValue() != null && !entry.getValue().isEmpty())
                .sorted(Map.Entry.comparingByKey())
                .map(entry -> entry.getKey() + "=" + entry.getValue())
                .collect(Collectors.joining("|"));
            
            return sha256Hash(combined);
            
        } catch (Exception e) {
            return "FALLBACK_" + System.currentTimeMillis();
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
                    macAddresses.append(mac.toString()).append(",");
                }
            }
            
            String result = macAddresses.toString();
            return result.endsWith(",") ? result.substring(0, result.length() - 1) : result;
            
        } catch (Exception e) {
            return "unknown_mac";
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
                           .append(totalSpace / (1024 * 1024 * 1024)) // GB
                           .append(",");
                }
            }
            
            String result = diskInfo.toString();
            return result.endsWith(",") ? result.substring(0, result.length() - 1) : result;
            
        } catch (Exception e) {
            return "unknown_disk";
        }
    }
    
    /**
     * SHA256哈希
     */
    private String sha256Hash(String input) throws Exception {
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
     * 生成许可证文件
     */
    public String generateLicenseFile(String fingerprint) throws Exception {
        
        // 构建许可证信息JSON
        StringBuilder licenseJson = new StringBuilder();
        licenseJson.append("{");
        licenseJson.append("\"licenseId\":\"LJWX-DEV-").append(System.currentTimeMillis()).append("\",");
        licenseJson.append("\"customerName\":\"灵境万象开发环境\",");
        licenseJson.append("\"customerId\":\"ljwx-dev-001\",");
        licenseJson.append("\"licenseType\":\"ENTERPRISE\",");
        licenseJson.append("\"startDate\":\"").append(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\",");
        licenseJson.append("\"endDate\":\"").append(LocalDateTime.now().plusYears(10).format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\",");
        licenseJson.append("\"hardwareFingerprint\":\"").append(fingerprint).append("\",");
        licenseJson.append("\"maxUsers\":1000,");
        licenseJson.append("\"maxDevices\":5000,");
        licenseJson.append("\"maxOrganizations\":100,");
        licenseJson.append("\"features\":[\"basic_health\",\"advanced_alert\",\"user_management\",\"device_management\",\"report_export\",\"api_access\"],");
        licenseJson.append("\"version\":\"1.0\",");
        licenseJson.append("\"createTime\":\"").append(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)).append("\",");
        licenseJson.append("\"remarks\":\"Development License for LJWX Health Management System\"");
        licenseJson.append("}");
        
        // 构建许可证容器
        StringBuilder containerJson = new StringBuilder();
        containerJson.append("{");
        containerJson.append("\"data\":\"").append(escapeJson(licenseJson.toString())).append("\",");
        containerJson.append("\"signature\":\"DEV_SIGNATURE_").append(System.currentTimeMillis()).append("\",");
        containerJson.append("\"algorithm\":\"SHA256withRSA\",");
        containerJson.append("\"timestamp\":").append(System.currentTimeMillis());
        containerJson.append("}");
        
        // Base64编码
        return Base64.getEncoder().encodeToString(containerJson.toString().getBytes());
    }
    
    /**
     * 转义JSON字符串
     */
    private String escapeJson(String str) {
        return str.replace("\\", "\\\\")
                  .replace("\"", "\\\"")
                  .replace("\n", "\\n")
                  .replace("\r", "\\r");
    }
}