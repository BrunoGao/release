package com.ljwx.watch.network;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.concurrent.locks.ReentrantLock;
import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 网络状态管理器
 * 统一管理网络连接状态、服务器可达性等，提供缓存和状态变化通知功能
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class NetworkStateManager {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "NetworkManager");
    
    private static NetworkStateManager instance;
    private static final ReentrantLock instanceLock = new ReentrantLock();
    
    // 组件实例
    private NetworkStateDetector networkDetector;
    private ServerReachabilityChecker serverChecker;
    
    // 状态缓存
    private NetworkState currentNetworkState = NetworkState.UNKNOWN;
    private long lastNetworkCheckTime = 0;
    private static final long NETWORK_CACHE_DURATION = 30000; // 30秒
    
    // 服务器状态缓存
    private Map<String, ServerReachabilityChecker.ServerStatus> serverStatusCache = new HashMap<>();
    private static final long SERVER_CACHE_DURATION = 60000; // 60秒
    
    // 状态变化监听器
    private List<NetworkStateChangeListener> listeners = new ArrayList<>();
    
    public enum NetworkState {
        WIFI_CONNECTED("WiFi已连接"),
        MOBILE_CONNECTED("移动网络已连接"),
        ETHERNET_CONNECTED("有线网络已连接"),
        OFFLINE("离线状态"),
        UNKNOWN("状态未知");
        
        private final String displayName;
        
        NetworkState(String displayName) {
            this.displayName = displayName;
        }
        
        public String getDisplayName() {
            return displayName;
        }
        
        public boolean isConnected() {
            return this != OFFLINE && this != UNKNOWN;
        }
    }
    
    /**
     * 网络状态变化监听器接口
     */
    public interface NetworkStateChangeListener {
        /**
         * 网络状态发生变化时的回调
         * @param oldState 旧状态
         * @param newState 新状态
         */
        void onNetworkStateChanged(NetworkState oldState, NetworkState newState);
        
        /**
         * 服务器状态发生变化时的回调
         * @param serverUrl 服务器URL
         * @param oldStatus 旧状态
         * @param newStatus 新状态
         */
        void onServerStatusChanged(String serverUrl, boolean oldStatus, boolean newStatus);
    }
    
    private NetworkStateManager() {
        networkDetector = new NetworkStateDetector();
        serverChecker = new ServerReachabilityChecker();
        HiLog.info(LABEL_LOG, "NetworkStateManager初始化完成");
    }
    
    /**
     * 获取单例实例 - 线程安全
     */
    public static NetworkStateManager getInstance() {
        if (instance == null) {
            instanceLock.lock();
            try {
                if (instance == null) {
                    instance = new NetworkStateManager();
                }
            } finally {
                instanceLock.unlock();
            }
        }
        return instance;
    }
    
    /**
     * 获取当前网络状态（带缓存优化）
     * @param context 应用上下文
     * @param forceRefresh 是否强制刷新
     * @return 当前网络状态
     */
    public NetworkState getCurrentNetworkState(Context context, boolean forceRefresh) {
        long currentTime = System.currentTimeMillis();
        
        // 检查缓存有效性
        if (!forceRefresh && 
            currentTime - lastNetworkCheckTime < NETWORK_CACHE_DURATION && 
            currentNetworkState != NetworkState.UNKNOWN) {
            HiLog.debug(LABEL_LOG, "使用缓存的网络状态: " + currentNetworkState.getDisplayName());
            return currentNetworkState;
        }
        
        // 重新检测网络状态
        NetworkState oldState = currentNetworkState;
        NetworkStateDetector.ConnectivityStatus connectivity = networkDetector.checkConnectivity(context);
        NetworkStateDetector.NetworkType networkType = networkDetector.getNetworkType(context);
        
        // 映射到统一的网络状态
        if (connectivity == NetworkStateDetector.ConnectivityStatus.DISCONNECTED) {
            currentNetworkState = NetworkState.OFFLINE;
        } else {
            switch (networkType) {
                case WIFI:
                    currentNetworkState = NetworkState.WIFI_CONNECTED;
                    break;
                case MOBILE:
                    currentNetworkState = NetworkState.MOBILE_CONNECTED;
                    break;
                case ETHERNET:
                    currentNetworkState = NetworkState.ETHERNET_CONNECTED;
                    break;
                default:
                    currentNetworkState = NetworkState.UNKNOWN;
                    break;
            }
        }
        
        lastNetworkCheckTime = currentTime;
        
        // 通知状态变化
        if (oldState != currentNetworkState) {
            HiLog.info(LABEL_LOG, "网络状态变化: " + oldState.getDisplayName() + " -> " + currentNetworkState.getDisplayName());
            notifyNetworkStateChanged(oldState, currentNetworkState);
        }
        
        return currentNetworkState;
    }
    
    /**
     * 获取当前网络状态（使用默认缓存策略）
     */
    public NetworkState getCurrentNetworkState(Context context) {
        return getCurrentNetworkState(context, false);
    }
    
    /**
     * 判断当前是否离线
     * @param context 应用上下文
     * @return 是否离线
     */
    public boolean isOffline(Context context) {
        NetworkState state = getCurrentNetworkState(context);
        boolean offline = !state.isConnected();
        
        if (offline) {
            HiLog.info(LABEL_LOG, "设备当前处于离线状态: " + state.getDisplayName());
        }
        
        return offline;
    }
    
    /**
     * 检查指定服务器是否可用（带缓存）
     * @param serverUrl 服务器URL
     * @param forceRefresh 是否强制刷新
     * @return 服务器是否可用
     */
    public boolean isServerAvailable(String serverUrl, boolean forceRefresh) {
        // 检查缓存
        ServerReachabilityChecker.ServerStatus cachedStatus = serverStatusCache.get(serverUrl);
        if (!forceRefresh && cachedStatus != null && 
            !cachedStatus.isStale(SERVER_CACHE_DURATION)) {
            HiLog.debug(LABEL_LOG, "使用缓存的服务器状态: " + serverUrl + " -> " + cachedStatus.isReachable());
            return cachedStatus.isReachable();
        }
        
        // 重新检测服务器状态
        boolean oldStatus = cachedStatus != null ? cachedStatus.isReachable() : false;
        ServerReachabilityChecker.ServerStatus newServerStatus = serverChecker.checkServerStatus(serverUrl);
        boolean newStatus = newServerStatus.isReachable();
        
        // 更新缓存
        serverStatusCache.put(serverUrl, newServerStatus);
        
        // 通知服务器状态变化
        if (cachedStatus != null && oldStatus != newStatus) {
            HiLog.info(LABEL_LOG, "服务器状态变化: " + serverUrl + " " + oldStatus + " -> " + newStatus);
            notifyServerStatusChanged(serverUrl, oldStatus, newStatus);
        }
        
        return newStatus;
    }
    
    /**
     * 检查服务器是否可用（使用默认缓存策略）
     */
    public boolean isServerAvailable(String serverUrl) {
        return isServerAvailable(serverUrl, false);
    }
    
    /**
     * 综合判断是否应该执行网络任务
     * @param context 应用上下文
     * @param serverUrl 目标服务器URL (可选)
     * @return 是否应该执行网络任务
     */
    public boolean shouldExecuteNetworkTask(Context context, String serverUrl) {
        // 第一步：检查本地网络连接
        if (isOffline(context)) {
            HiLog.info(LABEL_LOG, "本地网络离线，跳过网络任务");
            return false;
        }
        
        // 第二步：检查目标服务器可达性（如果提供了服务器URL）
        if (serverUrl != null && !serverUrl.isEmpty()) {
            if (!isServerAvailable(serverUrl)) {
                HiLog.info(LABEL_LOG, "目标服务器不可达，跳过网络任务: " + serverUrl);
                return false;
            }
        }
        
        HiLog.debug(LABEL_LOG, "网络条件满足，可以执行网络任务" + (serverUrl != null ? ": " + serverUrl : ""));
        return true;
    }
    
    /**
     * 只检查本地网络连接，不检查服务器
     * @param context 应用上下文
     * @return 是否应该执行网络任务
     */
    public boolean shouldExecuteNetworkTask(Context context) {
        return shouldExecuteNetworkTask(context, null);
    }
    
    /**
     * 获取网络质量信息
     * @param context 应用上下文
     * @return 网络质量信息
     */
    public NetworkStateDetector.NetworkQuality getNetworkQuality(Context context) {
        return networkDetector.getNetworkQuality(context);
    }
    
    /**
     * 清除所有缓存（强制重新检测）
     */
    public void clearCache() {
        currentNetworkState = NetworkState.UNKNOWN;
        lastNetworkCheckTime = 0;
        serverStatusCache.clear();
        HiLog.info(LABEL_LOG, "网络状态缓存已清除");
    }
    
    /**
     * 清除指定服务器的缓存
     */
    public void clearServerCache(String serverUrl) {
        serverStatusCache.remove(serverUrl);
        HiLog.info(LABEL_LOG, "已清除服务器缓存: " + serverUrl);
    }
    
    /**
     * 添加网络状态变化监听器
     */
    public void addNetworkStateChangeListener(NetworkStateChangeListener listener) {
        if (listener != null && !listeners.contains(listener)) {
            listeners.add(listener);
            HiLog.debug(LABEL_LOG, "已添加网络状态监听器，当前监听器数量: " + listeners.size());
        }
    }
    
    /**
     * 移除网络状态变化监听器
     */
    public void removeNetworkStateChangeListener(NetworkStateChangeListener listener) {
        if (listeners.remove(listener)) {
            HiLog.debug(LABEL_LOG, "已移除网络状态监听器，当前监听器数量: " + listeners.size());
        }
    }
    
    /**
     * 通知网络状态变化
     */
    private void notifyNetworkStateChanged(NetworkState oldState, NetworkState newState) {
        for (NetworkStateChangeListener listener : listeners) {
            try {
                listener.onNetworkStateChanged(oldState, newState);
            } catch (Exception e) {
                HiLog.error(LABEL_LOG, "通知网络状态变化异常: " + e.getMessage());
            }
        }
    }
    
    /**
     * 通知服务器状态变化
     */
    private void notifyServerStatusChanged(String serverUrl, boolean oldStatus, boolean newStatus) {
        for (NetworkStateChangeListener listener : listeners) {
            try {
                listener.onServerStatusChanged(serverUrl, oldStatus, newStatus);
            } catch (Exception e) {
                HiLog.error(LABEL_LOG, "通知服务器状态变化异常: " + e.getMessage());
            }
        }
    }
    
    /**
     * 获取网络状态诊断信息
     */
    public NetworkDiagnosticInfo getDiagnosticInfo(Context context) {
        NetworkState networkState = getCurrentNetworkState(context, true); // 强制刷新
        NetworkStateDetector.NetworkQuality quality = getNetworkQuality(context);
        
        Map<String, Boolean> serverStatus = new HashMap<>();
        for (String serverUrl : serverStatusCache.keySet()) {
            serverStatus.put(serverUrl, isServerAvailable(serverUrl));
        }
        
        return new NetworkDiagnosticInfo(networkState, quality, serverStatus);
    }
    
    /**
     * 获取缓存的服务器状态信息
     * @return 服务器状态缓存
     */
    public Map<String, ServerReachabilityChecker.ServerStatus> getCachedServerStatus() {
        return new HashMap<>(serverStatusCache);
    }
    
    /**
     * 网络诊断信息类
     */
    public static class NetworkDiagnosticInfo {
        private final NetworkState networkState;
        private final NetworkStateDetector.NetworkQuality networkQuality;
        private final Map<String, Boolean> serverStatus;
        private final long timestamp;
        
        public NetworkDiagnosticInfo(NetworkState networkState, 
                                   NetworkStateDetector.NetworkQuality networkQuality,
                                   Map<String, Boolean> serverStatus) {
            this.networkState = networkState;
            this.networkQuality = networkQuality;
            this.serverStatus = new HashMap<>(serverStatus);
            this.timestamp = System.currentTimeMillis();
        }
        
        public NetworkState getNetworkState() { return networkState; }
        public NetworkStateDetector.NetworkQuality getNetworkQuality() { return networkQuality; }
        public Map<String, Boolean> getServerStatus() { return new HashMap<>(serverStatus); }
        public long getTimestamp() { return timestamp; }
        
        @Override
        public String toString() {
            return String.format("NetworkDiagnostic{state=%s, quality=%s, servers=%d, time=%d}", 
                               networkState, networkQuality.getQuality(), 
                               serverStatus.size(), timestamp);
        }
    }
}