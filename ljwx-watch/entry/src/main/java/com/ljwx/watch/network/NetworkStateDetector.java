package com.ljwx.watch.network;

import ohos.net.NetManager;
import ohos.net.NetHandle;
import ohos.net.NetAllCapabilities;
import ohos.net.NetCapability;
import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 网络状态检测器
 * 负责检测设备的基础网络连接状态和网络质量
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class NetworkStateDetector {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "NetworkDetector");
    
    public enum NetworkType {
        WIFI("WiFi网络"),
        MOBILE("移动网络"), 
        ETHERNET("有线网络"),
        NONE("无网络连接");
        
        private final String displayName;
        
        NetworkType(String displayName) {
            this.displayName = displayName;
        }
        
        public String getDisplayName() {
            return displayName;
        }
    }
    
    public enum ConnectivityStatus {
        CONNECTED("已连接"),
        DISCONNECTED("已断开"),
        CONNECTING("连接中"),
        UNKNOWN("状态未知");
        
        private final String displayName;
        
        ConnectivityStatus(String displayName) {
            this.displayName = displayName;
        }
        
        public String getDisplayName() {
            return displayName;
        }
    }
    
    /**
     * 检测当前网络连接类型
     * @param context 应用上下文
     * @return 网络类型
     */
    public NetworkType getNetworkType(Context context) {
        try {
            NetManager netManager = NetManager.getInstance(context);
            NetHandle netHandle = netManager.getDefaultNet();
            
            if (netHandle == null) {
                HiLog.info(LABEL_LOG, "未找到默认网络连接");
                return NetworkType.NONE;
            }
            
            NetAllCapabilities capabilities = netManager.getNetCapabilities(netHandle);
            if (capabilities == null) {
                HiLog.info(LABEL_LOG, "无法获取网络能力信息");
                return NetworkType.NONE;
            }
            
            // 按优先级检测网络类型
            if (capabilities.hasTransport(NetCapability.NET_CAPABILITY_WIFI)) {
                HiLog.info(LABEL_LOG, "检测到WiFi网络连接");
                return NetworkType.WIFI;
            } else if (capabilities.hasTransport(NetCapability.NET_CAPABILITY_CELLULAR)) {
                HiLog.info(LABEL_LOG, "检测到移动网络连接");
                return NetworkType.MOBILE;
            } else if (capabilities.hasTransport(NetCapability.NET_CAPABILITY_ETHERNET)) {
                HiLog.info(LABEL_LOG, "检测到有线网络连接");
                return NetworkType.ETHERNET;
            }
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "网络类型检测异常: " + e.getMessage());
        }
        
        return NetworkType.NONE;
    }
    
    /**
     * 检测网络连通性状态
     * @param context 应用上下文
     * @return 连通性状态
     */
    public ConnectivityStatus checkConnectivity(Context context) {
        NetworkType networkType = getNetworkType(context);
        
        if (networkType == NetworkType.NONE) {
            return ConnectivityStatus.DISCONNECTED;
        }
        
        // 进一步检查网络是否真正可用
        boolean internetReachable = checkInternetReachability();
        return internetReachable ? ConnectivityStatus.CONNECTED : ConnectivityStatus.DISCONNECTED;
    }
    
    /**
     * 检查互联网可达性 - 使用多个测试点确保准确性
     * @return 是否可达互联网
     */
    private boolean checkInternetReachability() {
        String[] testHosts = {
            "8.8.8.8",          // Google DNS
            "114.114.114.114",  // 114 DNS  
            "1.1.1.1"           // Cloudflare DNS
        };
        
        int successCount = 0;
        for (String host : testHosts) {
            if (pingTest(host, 3000)) { // 3秒超时
                successCount++;
            }
            
            // 至少有一个测试点通过就认为网络可达
            if (successCount > 0) {
                HiLog.info(LABEL_LOG, "互联网连通性检测通过: " + host);
                return true;
            }
        }
        
        HiLog.warn(LABEL_LOG, "所有互联网连通性测试均失败");
        return false;
    }
    
    /**
     * Ping测试实现
     * @param host 目标主机
     * @param timeoutMs 超时时间(毫秒)
     * @return 是否ping通
     */
    private boolean pingTest(String host, int timeoutMs) {
        try {
            String command = String.format("ping -c 1 -W %d %s", timeoutMs / 1000, host);
            Process process = Runtime.getRuntime().exec(command);
            int exitCode = process.waitFor();
            
            if (exitCode == 0) {
                HiLog.debug(LABEL_LOG, "Ping测试成功: " + host);
                return true;
            } else {
                HiLog.debug(LABEL_LOG, "Ping测试失败: " + host + ", 退出码: " + exitCode);
                return false;
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "Ping测试异常: " + host + ", " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 获取网络质量信息
     * @param context 应用上下文
     * @return 网络质量描述
     */
    public NetworkQuality getNetworkQuality(Context context) {
        if (getNetworkType(context) == NetworkType.NONE) {
            return new NetworkQuality(0, "无网络连接", NetworkQuality.Quality.NONE);
        }
        
        // 使用ping延迟评估网络质量
        long avgLatency = measureAverageLatency();
        
        if (avgLatency < 100) {
            return new NetworkQuality(avgLatency, "网络质量优秀", NetworkQuality.Quality.EXCELLENT);
        } else if (avgLatency < 300) {
            return new NetworkQuality(avgLatency, "网络质量良好", NetworkQuality.Quality.GOOD);
        } else if (avgLatency < 1000) {
            return new NetworkQuality(avgLatency, "网络质量一般", NetworkQuality.Quality.FAIR);
        } else {
            return new NetworkQuality(avgLatency, "网络质量较差", NetworkQuality.Quality.POOR);
        }
    }
    
    /**
     * 测量平均网络延迟
     * @return 平均延迟(毫秒)
     */
    private long measureAverageLatency() {
        String testHost = "8.8.8.8";
        long totalLatency = 0;
        int successCount = 0;
        
        for (int i = 0; i < 3; i++) { // 测试3次取平均值
            long startTime = System.currentTimeMillis();
            if (pingTest(testHost, 2000)) {
                long latency = System.currentTimeMillis() - startTime;
                totalLatency += latency;
                successCount++;
            }
        }
        
        return successCount > 0 ? totalLatency / successCount : Long.MAX_VALUE;
    }
    
    /**
     * 网络质量信息类
     */
    public static class NetworkQuality {
        public enum Quality {
            EXCELLENT, GOOD, FAIR, POOR, NONE
        }
        
        private final long latency;
        private final String description;
        private final Quality quality;
        
        public NetworkQuality(long latency, String description, Quality quality) {
            this.latency = latency;
            this.description = description;
            this.quality = quality;
        }
        
        public long getLatency() { return latency; }
        public String getDescription() { return description; }
        public Quality getQuality() { return quality; }
        
        @Override
        public String toString() {
            return String.format("NetworkQuality{latency=%dms, quality=%s, desc='%s'}", 
                               latency, quality, description);
        }
    }
}