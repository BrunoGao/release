package com.ljwx.watch.network;

import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 服务器可达性检测器
 * 负责检测指定服务器的可达性和响应状态
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class ServerReachabilityChecker {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "ServerChecker");
    
    // 连接超时配置
    private static final int CONNECTION_TIMEOUT = 5000; // 5秒
    private static final int READ_TIMEOUT = 3000;       // 3秒
    
    // 健康检查端点后缀
    private static final String HEALTH_CHECK_ENDPOINT = "/health";
    private static final String PING_ENDPOINT = "/ping";
    
    /**
     * 检测单个服务器是否可达
     * @param serverUrl 服务器URL
     * @return 是否可达
     */
    public boolean isServerReachable(String serverUrl) {
        return checkServerEndpoint(serverUrl, HEALTH_CHECK_ENDPOINT) ||
               checkServerEndpoint(serverUrl, PING_ENDPOINT) ||
               checkServerEndpoint(serverUrl, ""); // 检查根路径
    }
    
    /**
     * 检测指定服务器端点
     * @param serverUrl 服务器基础URL
     * @param endpoint 端点路径
     * @return 是否可达
     */
    private boolean checkServerEndpoint(String serverUrl, String endpoint) {
        HttpURLConnection connection = null;
        try {
            String fullUrl = serverUrl + endpoint;
            URL url = new URL(fullUrl);
            connection = (HttpURLConnection) url.openConnection();
            
            // 配置连接参数
            connection.setRequestMethod("HEAD"); // 使用HEAD减少数据传输
            connection.setConnectTimeout(CONNECTION_TIMEOUT);
            connection.setReadTimeout(READ_TIMEOUT);
            connection.setInstanceFollowRedirects(false);
            connection.setRequestProperty("User-Agent", "LJWX-Watch/1.0");
            
            // 执行连接
            long startTime = System.currentTimeMillis();
            int responseCode = connection.getResponseCode();
            long responseTime = System.currentTimeMillis() - startTime;
            
            boolean isReachable = isValidResponseCode(responseCode);
            
            HiLog.info(LABEL_LOG, String.format("服务器检测: %s, 响应码: %d, 耗时: %dms, 可达: %s", 
                                               fullUrl, responseCode, responseTime, isReachable));
            
            return isReachable;
            
        } catch (java.net.SocketTimeoutException e) {
            HiLog.warn(LABEL_LOG, "服务器连接超时: " + serverUrl + endpoint);
            return false;
        } catch (java.net.ConnectException e) {
            HiLog.warn(LABEL_LOG, "服务器连接被拒绝: " + serverUrl + endpoint);
            return false;
        } catch (java.net.UnknownHostException e) {
            HiLog.warn(LABEL_LOG, "服务器域名解析失败: " + serverUrl + endpoint);
            return false;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "服务器检测异常: " + serverUrl + endpoint + ", " + e.getMessage());
            return false;
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }
    
    /**
     * 判断HTTP响应码是否表示服务器可达
     * @param responseCode HTTP响应码
     * @return 是否表示可达
     */
    private boolean isValidResponseCode(int responseCode) {
        // 2xx: 成功
        // 3xx: 重定向 (服务器可达但可能需要跳转)
        // 401/403: 权限问题但服务器可达
        // 404: 端点不存在但服务器可达
        // 405: 方法不允许但服务器可达
        return (responseCode >= 200 && responseCode < 400) ||
               responseCode == 401 || responseCode == 403 ||
               responseCode == 404 || responseCode == 405;
    }
    
    /**
     * 批量检测多个服务器的可达性
     * @param serverUrls 服务器URL列表
     * @return 检测结果映射
     */
    public Map<String, ServerStatus> checkMultipleServers(List<String> serverUrls) {
        Map<String, ServerStatus> results = new HashMap<>();
        
        for (String url : serverUrls) {
            long startTime = System.currentTimeMillis();
            boolean isReachable = isServerReachable(url);
            long responseTime = System.currentTimeMillis() - startTime;
            
            results.put(url, new ServerStatus(isReachable, responseTime));
        }
        
        return results;
    }
    
    /**
     * 检测服务器可达性并返回详细状态
     * @param serverUrl 服务器URL
     * @return 服务器状态信息
     */
    public ServerStatus checkServerStatus(String serverUrl) {
        long startTime = System.currentTimeMillis();
        boolean isReachable = isServerReachable(serverUrl);
        long responseTime = System.currentTimeMillis() - startTime;
        
        return new ServerStatus(isReachable, responseTime);
    }
    
    /**
     * 服务器状态信息类
     */
    public static class ServerStatus {
        private final boolean reachable;
        private final long responseTime;
        private final long checkTime;
        
        public ServerStatus(boolean reachable, long responseTime) {
            this.reachable = reachable;
            this.responseTime = responseTime;
            this.checkTime = System.currentTimeMillis();
        }
        
        public boolean isReachable() { return reachable; }
        public long getResponseTime() { return responseTime; }
        public long getCheckTime() { return checkTime; }
        
        /**
         * 判断状态信息是否过期
         * @param maxAgeMs 最大有效期(毫秒)
         * @return 是否过期
         */
        public boolean isStale(long maxAgeMs) {
            return System.currentTimeMillis() - checkTime > maxAgeMs;
        }
        
        /**
         * 获取状态信息的年龄(毫秒)
         * @return 状态信息年龄
         */
        public long getAge() {
            return System.currentTimeMillis() - checkTime;
        }
        
        @Override
        public String toString() {
            return String.format("ServerStatus{reachable=%s, responseTime=%dms, age=%ds}", 
                               reachable, responseTime, 
                               (System.currentTimeMillis() - checkTime) / 1000);
        }
    }
}