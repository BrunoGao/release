package com.ljwx.watch;

import com.ljwx.watch.utils.Utils;
import com.ljwx.watch.utils.CustomLogger;
import com.ljwx.watch.network.NetworkStateManager;
import ohos.aafwk.ability.Ability;
import ohos.aafwk.content.Intent;
import ohos.app.Context;
import com.tdtech.ohos.mdm.DeviceManager;
import ohos.batterymanager.BatteryInfo;
import ohos.data.DatabaseHelper;
import ohos.data.preferences.Preferences;
import ohos.event.notification.NotificationHelper;
import ohos.event.notification.NotificationRequest;
import ohos.rpc.IRemoteObject;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Timer;
import java.util.TimerTask;
import java.nio.charset.StandardCharsets;
import com.ljwx.watch.utils.DataManager;
import ohos.rpc.RemoteException;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONArray;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.lang.Thread;
import java.util.Iterator;

/**
 * 增强版HttpService - 集成智能离线检测和网络状态管理
 * 
 * @author ljwx-tech
 * @version 2.0
 */
public class HttpServiceEnhanced extends Ability implements NetworkStateManager.NetworkStateChangeListener {
    private static HttpServiceEnhanced instance;
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "ljwx-http-enhanced");

    // 数据管理器
    private DataManager dataManager = DataManager.getInstance();
    
    // 网络状态管理器 - 新增
    private NetworkStateManager networkStateManager;

    // 设备管理器
    private DeviceManager deviceManager = null;

    // 设备信息
    private String deviceSn = "";
    private String customerId = "0";
    private String customerName = "云祥灵境";
    private String currentDeviceInfo = "";
    private String lastDeviceInfo = "";
    private String lastCommonEvent = "";

    // API认证信息
    private String apiId = "";
    private String apiAuthorization = "";

    // 接口URL
    private String platformUrl = null;
    private String fetchMessageUrl = null;
    private String uploadDeviceUrl = null;
    private String uploadCommonEventUrl = null;
    private String fetchConfigUrl = null;

    // 接口间隔时间（秒）
    private int fetchConfigInterval = 0;
    private int uploadHealthInterval = 600;
    private int uploadDeviceInterval = 18000;
    private int fetchMessageInterval = 60;
    private int uploadCommonEventInterval = 0;

    // 接口启用状态
    private boolean fetchMessageEnabled = false;
    private boolean uploadHealthEnabled = true;
    private boolean uploadDeviceEnabled = true;
    private boolean uploadCommonEventEnabled = false;
    private boolean fetchConfigEnabled = false;

    // 通知ID
    private static int notificationId = 2000;

    // 电池信息
    private BatteryInfo batteryInfo;

    // 消息类型映射
    private static final Map<String, String> MESSAGE_TYPE_MAP = new HashMap<>();
    static {
        MESSAGE_TYPE_MAP.put("announcement", "公告");
        MESSAGE_TYPE_MAP.put("notification", "个人通知");
        MESSAGE_TYPE_MAP.put("warning", "告警");
        MESSAGE_TYPE_MAP.put("job", "作业指引");
        MESSAGE_TYPE_MAP.put("task", "任务管理");
    }

    // 统一定时器
    private Timer masterHttpTimer;
    private long httpTick = 0;
    private final int baseHttpPeriod = 5; // 基础周期5秒

    // 数据缓存相关
    private static String lastHealthInfo;
    private static String lastBTHealthInfo;
    private static String lastBTDeviceInfo;
    private static long lastHealthUpdateTime;
    private static long lastDeviceUpdateTime;
    private static final long HEALTH_CACHE_DURATION = 5000; // 5秒缓存
    private static final long DEVICE_CACHE_DURATION = 60000; // 1分钟缓存

    // 防重复处理机制
    private static final Map<String, Long> lastEventTimeMap = new HashMap<>();
    private static final long EVENT_DEDUP_INTERVAL = 1000; // 1秒防重复间隔

    // Preferences缓存
    private Preferences preferences;

    // 健康数据缓存
    private HealthDataCache healthDataCache;
    
    // 网络重试策略配置 - 新增
    private static final int NETWORK_RETRY_BASE_INTERVAL = 60000; // 基础重试间隔1分钟
    private static final int NETWORK_RETRY_MAX_INTERVAL = 1800000; // 最大重试间隔30分钟
    private static final int NETWORK_RETRY_MULTIPLIER = 2; // 重试间隔倍数

    public HttpServiceEnhanced() {
        // 初始化网络状态管理器
        networkStateManager = NetworkStateManager.getInstance();
        
        // 注册网络状态变化监听
        networkStateManager.addNetworkStateChangeListener(this);
        
        // 注册属性变化监听器
        dataManager.addPropertyChangeListener(evt -> {
            HiLog.info(LABEL_LOG, "PropertyChangeListener:" + evt.getPropertyName());
            if("wearState".equals(evt.getPropertyName())){
                HiLog.info(LABEL_LOG, "HttpServiceEnhanced:: uploadDeviceInfo by wearState change" + dataManager.getWearState());
                uploadDeviceInfoSmart();
            }else if("commonEvent".equals(evt.getPropertyName())){
                String commonEvent = dataManager.getCommonEvent();
                HiLog.info(LABEL_LOG, "HttpServiceEnhanced::onPropertyChange commonEvent: " + commonEvent);
                uploadCommonEventSmart(commonEvent);
            }else if("config".equals(evt.getPropertyName())){
                HiLog.info(LABEL_LOG, "HttpServiceEnhanced::onPropertyChange got config, initHttpParameters");
            }
        });

        healthDataCache = HealthDataCache.getInstance();
    }

    @Override
    public void onStart(Intent intent) {
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::onStart");
        super.onStart(intent);
        
        // 初始化Utils
        Utils.init(getContext());
        
        // 初始化自定义日志系统
        CustomLogger.info("HttpServiceEnhanced::onStart", "启动增强版HTTP服务，集成智能离线检测");
        
        // 设置后台运行通知
        setupBackgroundNotification();
        startTimers();
        showNotification("启动增强版HTTP服务");
    }

    // 网络状态变化回调 - 新增
    @Override
    public void onNetworkStateChanged(NetworkStateManager.NetworkState oldState, 
                                    NetworkStateManager.NetworkState newState) {
        HiLog.info(LABEL_LOG, "网络状态变化回调: " + oldState.getDisplayName() + " -> " + newState.getDisplayName());
        
        if (oldState == NetworkStateManager.NetworkState.OFFLINE && newState.isConnected()) {
            // 网络恢复，立即尝试重传缓存数据
            HiLog.info(LABEL_LOG, "网络恢复，开始重传缓存数据");
            retryAllCachedDataImmediate();
        } else if (newState == NetworkStateManager.NetworkState.OFFLINE) {
            // 网络断开，记录日志
            HiLog.warn(LABEL_LOG, "网络已断开，后续网络任务将被跳过");
        }
    }

    // 服务器状态变化回调 - 新增
    @Override
    public void onServerStatusChanged(String serverUrl, boolean oldStatus, boolean newStatus) {
        HiLog.info(LABEL_LOG, "服务器状态变化回调: " + serverUrl + " " + oldStatus + " -> " + newStatus);
        
        if (!oldStatus && newStatus) {
            // 服务器恢复，尝试重传相关缓存数据
            HiLog.info(LABEL_LOG, "服务器恢复，尝试重传相关数据: " + serverUrl);
            retryDataForServer(serverUrl);
        }
    }

    // 设置后台运行通知
    private void setupBackgroundNotification() {
        NotificationRequest request = new NotificationRequest(1005);
        NotificationRequest.NotificationNormalContent content = new NotificationRequest.NotificationNormalContent();
        content.setTitle("HttpServiceEnhanced").setText("keepServiceAlive");
        NotificationRequest.NotificationContent notificationContent = new NotificationRequest.NotificationContent(content);
        request.setContent(notificationContent);

        // 绑定通知
        keepBackgroundRunning(1005, request);

        // 获取通知ID
        String storedNotificationId = fetchValue("notificationId");
        if (storedNotificationId.isEmpty()) {
            notificationId = 2000; // 默认值
            storeValue("notificationId", String.valueOf(notificationId));
        } else {
            notificationId = Integer.parseInt(storedNotificationId);
        }
    }

    // 启动定时任务
    private void startTimers() {
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::startTimers");
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::startTimers uploadDeviceInterval: " + dataManager.getUploadDeviceInterval());
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::startTimers uploadHealthInterval: " + dataManager.getUploadHealthInterval());
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::startTimers fetchMessageInterval: " + dataManager.getFetchMessageInterval());
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::startTimers uploadCommonEventInterval: " + dataManager.getUploadCommonEventInterval());
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::startTimers fetchConfigInterval: " + dataManager.getFetchConfigInterval());

        // 统一定时器调度 - 60秒基础周期
        if (shouldStartNetworkTasks()) {
            masterHttpTimer = new Timer();
            int uploadHealthInterval = dataManager.getUploadHealthInterval();
            int uploadDeviceInterval = dataManager.getUploadDeviceInterval();
            int fetchMessageInterval = dataManager.getFetchMessageInterval();
            int uploadCommonEventInterval = dataManager.getUploadCommonEventInterval();
            int fetchConfigInterval = dataManager.getFetchConfigInterval();
            
            masterHttpTimer.schedule(new TimerTask() {
                @Override
                public void run() {
                    httpTick++;
                    
                    // 检查网络状态，智能决定是否执行任务
                    if (!networkStateManager.shouldExecuteNetworkTask(getContext())) {
                        HiLog.debug(LABEL_LOG, "网络不可用，跳过本轮网络任务");
                        return;
                    }
                    
                    // 上传健康数据 - 每10分钟执行
                    if (uploadHealthInterval > 0 && httpTick % (uploadHealthInterval / baseHttpPeriod) == 0) {
                        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::masterTimer 执行健康数据批量上传");
                        uploadHealthDataSmart();
                    }
                    
                    // 上传设备信息 - 根据配置周期执行
                    if (uploadDeviceInterval> 0 && httpTick % (uploadDeviceInterval / baseHttpPeriod) == 0) {
                        uploadDeviceInfoSmart();
                    }
                    
                    // 获取消息 - 根据配置周期执行
                    if (fetchMessageInterval > 0 && httpTick % (fetchMessageInterval / baseHttpPeriod) == 0) {
                        fetchMessageFromServerSmart();
                    }
                    
                    // 缓存数据重传检查 - 每2分钟执行一次
                    if (httpTick % (120 / baseHttpPeriod) == 0) {
                        checkAndRetryCachedDataSmart();
                    }
                    
                    // 防止计数器溢出
                    if (httpTick >= 1440) httpTick = 0; // 24小时重置
                }
            }, 0, baseHttpPeriod * 1000);
        } else {
            HiLog.warn(LABEL_LOG, "HttpServiceEnhanced::startTimers 网络条件不满足，跳过定时器启动");
        }
    }

    /**
     * 判断是否应该启动网络任务 - 新增
     */
    private boolean shouldStartNetworkTasks() {
        // 检查上传方法配置
        if (!"wifi".equals(dataManager.getUploadMethod())) {
            HiLog.info(LABEL_LOG, "非WiFi模式，网络任务将在条件满足时启动");
            return false;
        }
        
        // 检查基础网络条件
        return networkStateManager.shouldExecuteNetworkTask(getContext());
    }

    /**
     * 智能健康数据上传 - 增强版
     */
    public void uploadHealthDataSmart() {
        if(dataManager.getHeartRate() == 1000){
            CustomLogger.info("HttpServiceEnhanced::uploadHealthDataSmart", "心率是0，不上传健康数据");
            return;
        }
        
        String currentHealthInfo = Utils.getHealthInfo();
        if (currentHealthInfo != null && !currentHealthInfo.isEmpty()) {
            // 记录健康数据详情
            CustomLogger.logHealthInfo("准备智能上传健康数据", currentHealthInfo);
            
            // 先缓存数据
            healthDataCache.addToCache(currentHealthInfo);
            CustomLogger.info("HttpServiceEnhanced::uploadHealthDataSmart", "数据已缓存");
        } else {
            CustomLogger.warn("HttpServiceEnhanced::uploadHealthDataSmart", "健康数据无效，跳过上传");
            return;
        }
        
        // 智能判断是否上传
        if (!dataManager.isLicenseExceeded()) {
            if (networkStateManager.shouldExecuteNetworkTask(getContext(), dataManager.getUploadHealthDataUrl())) {
                CustomLogger.info("HttpServiceEnhanced::uploadHealthDataSmart", "网络条件满足，开始批量上传缓存数据");
                boolean uploadSuccess = uploadAllCachedDataSmart();
                if(!uploadSuccess && dataManager.isEnableResume()){
                    CustomLogger.error("HttpServiceEnhanced::uploadHealthDataSmart", "批量上传失败，数据保留在缓存中等待智能重传");
                }
            } else {
                CustomLogger.warn("HttpServiceEnhanced::uploadHealthDataSmart", "网络条件不满足，数据已缓存等待网络恢复");
            }
        } else {
            CustomLogger.warn("HttpServiceEnhanced::uploadHealthDataSmart", "许可证超限，数据已缓存等待条件满足");
        }
    }

    /**
     * 智能批量上传缓存数据 - 增强版
     */
    private boolean uploadAllCachedDataSmart() {
        List<String> cachedData = healthDataCache.getAllCachedData();
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadAllCachedDataSmart 开始智能上传缓存数据，数量: " + cachedData.size());
        
        if (cachedData.isEmpty()) {
            return true;
        }

        // 检查网络状态
        if (!networkStateManager.shouldExecuteNetworkTask(getContext(), dataManager.getUploadHealthDataUrl())) {
            HiLog.warn(LABEL_LOG, "网络条件不满足，暂停批量上传");
            return false;
        }

        int retryCount = 0;
        boolean success = false;
        
        while (retryCount < dataManager.getUploadRetryCount() && !success) {
            try {
                // 构建统一格式的JSON数据
                JSONObject finalJson = new JSONObject();
                if (cachedData.size() == 1) {
                    // 单条数据，直接使用原始数据
                    finalJson = new JSONObject(cachedData.get(0));
                } else {
                    // 批量数据，提取每个对象中的data字段内容
                    JSONArray jsonArray = new JSONArray();
                    for (String data : cachedData) {
                        try {
                            JSONObject jsonObj = new JSONObject(data);
                            JSONObject dataContent = jsonObj.getJSONObject("data");
                            jsonArray.put(dataContent);
                        } catch (JSONException e) {
                            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadAllCachedDataSmart 解析JSON失败: " + e.getMessage());
                            continue;
                        }
                    }
                    finalJson.put("data", jsonArray);
                }
                
                String uploadData = finalJson.toString();
                CustomLogger.logLongData("HttpServiceEnhanced::uploadAllCachedDataSmart", "准备智能上传的完整缓存数据", uploadData);
                
                // 尝试上传
                success = uploadDataSmart(dataManager.getUploadHealthDataUrl(), uploadData);
                
                if (success) {
                    // 上传成功，清空缓存
                    healthDataCache.clearCache();
                    HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadAllCachedDataSmart 智能批量上传成功");
                } else {
                    retryCount++;
                    HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadAllCachedDataSmart 上传失败，重试次数: " + retryCount);
                    // 等待一段时间后重试
                    Thread.sleep(1000 * retryCount);
                }
            } catch (Exception e) {
                HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadAllCachedDataSmart error: " + e.getMessage());
                retryCount++;
                try {
                    Thread.sleep(1000 * retryCount);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        
        if (!success) {
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadAllCachedDataSmart 达到最大重试次数，智能上传失败");
        }
        
        return success;
    }

    /**
     * 智能数据上传方法 - 增强版
     */
    private boolean uploadDataSmart(String targetUrl, String data) {
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: targetUrl: " + targetUrl);
        CustomLogger.logLongData("HttpServiceEnhanced::uploadDataSmart", "智能上传数据内容", data);
        
        // 首先检查网络条件
        if (!networkStateManager.shouldExecuteNetworkTask(getContext(), targetUrl)) {
            HiLog.warn(LABEL_LOG, "网络条件不满足，取消上传: " + targetUrl);
            return false;
        }
        
        boolean result = false;
        HttpURLConnection connection = null;
        try {
            URL url = new URL(targetUrl);
            connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(10000); // 10秒连接超时
            connection.setReadTimeout(10000);    // 10秒读取超时
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Authorization", dataManager.getApiAuthorization());
            connection.setDoOutput(true);

            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = data.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
                os.flush();
            }

            int responseCode = connection.getResponseCode();
            HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: POST Response Code :: " + responseCode);

            if (responseCode == 200) {
                HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: 智能上传成功: " + targetUrl);
                result = true;
                
                // 上传成功，清除对应服务器的缓存状态
                networkStateManager.clearServerCache(targetUrl);
            } else {
                // 读取错误响应内容
                String errorResponse = "";
                try (InputStream is = connection.getErrorStream()) {
                    if (is != null) {
                        ByteArrayOutputStream errorStream = new ByteArrayOutputStream();
                        byte[] buffer = new byte[1024];
                        int length;
                        while ((length = is.read(buffer)) != -1) {
                            errorStream.write(buffer, 0, length);
                        }
                        errorResponse = errorStream.toString(StandardCharsets.UTF_8.name());
                    }
                } catch (Exception ex) {
                    HiLog.error(LABEL_LOG, "读取错误响应失败: " + ex.getMessage());
                }
                HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: 智能上传失败: " + targetUrl + ", 响应码: " + responseCode + ", 错误内容: " + errorResponse);
            }
        } catch (java.net.ConnectException e) {
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: 连接被拒绝: " + targetUrl + ", 错误: " + e.getMessage());
            // 标记服务器为不可达
            networkStateManager.clearServerCache(targetUrl);
        } catch (java.net.SocketTimeoutException e) {
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: 连接超时: " + targetUrl + ", 错误: " + e.getMessage());
        } catch (java.net.UnknownHostException e) {
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: 未知主机: " + targetUrl + ", 错误: " + e.getMessage());
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadDataSmart :: 智能上传异常: " + targetUrl + ", 错误类型: " + e.getClass().getSimpleName() + ", 错误: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
        return result;
    }

    /**
     * 智能设备信息上传 - 增强版
     */
    private void uploadDeviceInfoSmart() {
        String currentDeviceInfo = Utils.getDeviceInfo();
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadDeviceInfoSmart currentDeviceInfo: " + currentDeviceInfo);
        
        if(currentDeviceInfo == null || currentDeviceInfo.isEmpty()){
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadDeviceInfoSmart currentDeviceInfo is null or empty");
            return;
        }
        
        if(!"wifi".equals(dataManager.getUploadMethod())){
            HiLog.info(LABEL_LOG, "非WiFi模式，跳过设备信息上传");
            return;
        }
        
        if (!currentDeviceInfo.equals(lastDeviceInfo)) {
            // 检查网络条件
            if (networkStateManager.shouldExecuteNetworkTask(getContext(), dataManager.getUploadDeviceInfoUrl())) {
                boolean success = uploadDeviceInfoWithCacheSmart(currentDeviceInfo);
                if (success) {
                    lastDeviceInfo = currentDeviceInfo;
                }
            } else {
                HiLog.info(LABEL_LOG, "网络条件不满足，设备信息上传将在网络恢复后进行");
            }
        }
    }

    /**
     * 智能设备信息缓存上传 - 增强版
     */
    private boolean uploadDeviceInfoWithCacheSmart(String deviceInfoData) {
        try {
            CustomLogger.logDeviceInfo("准备智能上传设备信息", deviceInfoData);
            
            // 1. 先缓存数据到设备信息专用缓存
            healthDataCache.addToCache(HealthDataCache.DataType.DEVICE_INFO, deviceInfoData);
            CustomLogger.info("HttpServiceEnhanced::uploadDeviceInfoWithCacheSmart", "设备信息已缓存");
            
            // 2. 检查网络条件并尝试上传
            if (networkStateManager.shouldExecuteNetworkTask(getContext(), dataManager.getUploadDeviceInfoUrl())) {
                boolean success = uploadDataSmart(dataManager.getUploadDeviceInfoUrl(), deviceInfoData);
                
                if (success) {
                    // 3. 上传成功，清除设备信息缓存
                    healthDataCache.clearCache(HealthDataCache.DataType.DEVICE_INFO);
                    CustomLogger.info("HttpServiceEnhanced::uploadDeviceInfoWithCacheSmart", "设备信息智能上传成功，缓存已清除");
                    return true;
                } else {
                    CustomLogger.warn("HttpServiceEnhanced::uploadDeviceInfoWithCacheSmart", "设备信息智能上传失败，数据保留在缓存中");
                    return false;
                }
            } else {
                CustomLogger.warn("HttpServiceEnhanced::uploadDeviceInfoWithCacheSmart", "网络条件不满足，设备信息已缓存等待上传");
                return false;
            }
        } catch (Exception e) {
            CustomLogger.error("HttpServiceEnhanced::uploadDeviceInfoWithCacheSmart", "错误: " + e.getMessage());
            return false;
        }
    }

    /**
     * 智能通用事件上传 - 增强版
     */
    public void uploadCommonEventSmart(String commonEvent) {
        // 在后台线程执行网络操作
        new Thread(() -> {
            try {
                JSONObject commonEventJson = new JSONObject();
                String[] parts = commonEvent.split(":");
                
                String commonEventType = parts[0];
                String commonEventValue = parts[1];
                
                // 防重复处理检查
                long currentTime = System.currentTimeMillis();
                Long lastTime = lastEventTimeMap.get(commonEventType);
                if (lastTime != null && (currentTime - lastTime) < EVENT_DEDUP_INTERVAL) {
                    HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadCommonEventSmart 跳过重复事件: " + commonEventType + " (间隔: " + (currentTime - lastTime) + "ms)");
                    return;
                }
                lastEventTimeMap.put(commonEventType, currentTime);
                
                DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
                String timestamp = Instant.now().atZone(ZoneId.systemDefault()).format(formatter);
                HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadCommonEventSmart commonEventType: " + commonEventType);
                HiLog.info(LABEL_LOG, "HttpServiceEnhanced::uploadCommonEventSmart commonEventValue: " + commonEventValue);

                commonEventJson.put("eventType", commonEventType);
                commonEventJson.put("eventValue", commonEventValue);
                commonEventJson.put("deviceSn", dataManager.getDeviceSn());
                
                // 添加客户信息字段
                if (dataManager.getCustomerId() != null) {
                    commonEventJson.put("customer_id", dataManager.getCustomerId());
                }
                if (dataManager.getOrgId() != null) {
                    commonEventJson.put("org_id", dataManager.getOrgId());
                }
                if (dataManager.getUserId() != null) {
                    commonEventJson.put("user_id", dataManager.getUserId());
                }
                
                commonEventJson.put("latitude", dataManager.getLatitude());
                commonEventJson.put("longitude", dataManager.getLongitude());
                commonEventJson.put("altitude", dataManager.getAltitude());
                commonEventJson.put("timestamp", timestamp);
                
                // 添加健康数据
                String healthInfoStr = Utils.getHealthInfoForCommonEvent();
                if (healthInfoStr != null && !healthInfoStr.isEmpty()) {
                    try {
                        JSONObject healthDataObj = new JSONObject(healthInfoStr);
                        commonEventJson.put("healthData", healthDataObj);
                        CustomLogger.logHealthInfo("通用事件内嵌健康数据", healthInfoStr);
                    } catch (JSONException e) {
                        CustomLogger.error("HttpServiceEnhanced::uploadCommonEventSmart", "解析healthData JSON失败: " + e.getMessage());
                        commonEventJson.put("healthData", healthInfoStr);
                    }
                } else {
                    CustomLogger.warn("HttpServiceEnhanced::uploadCommonEventSmart", "健康数据无效，不上传healthData字段");
                }

                String commonEventData = commonEventJson.toString();
                CustomLogger.logLongData("HttpServiceEnhanced::uploadCommonEventSmart", 
                    "🚀 智能通用事件完整数据", commonEventData);
                
                // 检查网络条件
                if (!networkStateManager.shouldExecuteNetworkTask(getContext(), dataManager.getUploadCommonEventUrl())) {
                    HiLog.warn(LABEL_LOG, "HttpServiceEnhanced::uploadCommonEventSmart 网络条件不满足，事件已缓存");
                    return;
                }

                // 处理特殊事件类型
                if(commonEventType.equalsIgnoreCase("com.tdtech.ohos.action.WEAR_STATUS_CHANGED")){
                    String deviceInfo = Utils.getDeviceInfo();
                    JSONObject deviceInfoJson = new JSONObject(deviceInfo);
                    deviceInfoJson.put("wearState", commonEventValue);
                    dataManager.setWearState(Integer.parseInt(commonEventValue));

                    HiLog.info(LABEL_LOG, "HttpServiceEnhanced::WEAR_STATUS_CHANGED.uploadDeviceInfo deviceInfo: " + deviceInfoJson.toString());
                    deviceInfo = deviceInfoJson.toString();
                    
                    boolean success = uploadDeviceInfoWithCacheSmart(deviceInfo);
                    if (!success) {
                        HiLog.error(LABEL_LOG, "HttpServiceEnhanced::WEAR_STATUS_CHANGED.uploadDeviceInfo 设备信息智能上传失败，已缓存: " + deviceInfo);
                    }
                }
                
                // 使用智能通用事件上传
                boolean success = uploadCommonEventWithCacheSmart(commonEventData);
                if (!success) {
                    HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadCommonEventSmart 通用事件智能上传失败，已缓存数据");
                }
            } catch (Exception e) {
                HiLog.error(LABEL_LOG, "HttpServiceEnhanced::uploadCommonEventSmart 异常: " + e.getMessage());
                e.printStackTrace();
            }
        }).start();
    }

    /**
     * 智能通用事件缓存上传 - 增强版
     */
    private boolean uploadCommonEventWithCacheSmart(String commonEventData) {
        try {
            // 记录通用事件详情
            try {
                JSONObject eventJson = new JSONObject(commonEventData);
                String deviceInfo = eventJson.has("deviceInfo") ? eventJson.get("deviceInfo").toString() : null;
                String healthInfo = eventJson.has("healthData") ? eventJson.get("healthData").toString() : null;
                CustomLogger.logCommonEvent("准备智能上传通用事件", deviceInfo, healthInfo);
            } catch (Exception e) {
                CustomLogger.warn("HttpServiceEnhanced::uploadCommonEventWithCacheSmart", "解析通用事件数据失败: " + e.getMessage());
            }
            
            // 1. 先缓存数据
            healthDataCache.addToCache(HealthDataCache.DataType.COMMON_EVENT, commonEventData);
            CustomLogger.info("HttpServiceEnhanced::uploadCommonEventWithCacheSmart", "通用事件已缓存");
            
            // 2. 检查网络条件并尝试上传
            if (networkStateManager.shouldExecuteNetworkTask(getContext(), dataManager.getUploadCommonEventUrl())) {
                boolean success = uploadDataSmart(dataManager.getUploadCommonEventUrl(), commonEventData);
                
                if (success) {
                    // 3. 上传成功，清除通用事件缓存
                    healthDataCache.clearCache(HealthDataCache.DataType.COMMON_EVENT);
                    CustomLogger.info("HttpServiceEnhanced::uploadCommonEventWithCacheSmart", "通用事件智能上传成功，缓存已清除");
                    return true;
                } else {
                    CustomLogger.warn("HttpServiceEnhanced::uploadCommonEventWithCacheSmart", "通用事件智能上传失败，数据保留在缓存中");
                    return false;
                }
            } else {
                CustomLogger.warn("HttpServiceEnhanced::uploadCommonEventWithCacheSmart", "网络条件不满足，通用事件已缓存等待上传");
                return false;
            }
        } catch (Exception e) {
            CustomLogger.error("HttpServiceEnhanced::uploadCommonEventWithCacheSmart", "错误: " + e.getMessage());
            return false;
        }
    }

    /**
     * 智能消息获取 - 增强版
     */
    public void fetchMessageFromServerSmart() {
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::fetchMessageFromServerSmart fetchMessageUrl: " + dataManager.getFetchMessageUrl());
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::fetchMessageFromServerSmart deviceSn: " + dataManager.getDeviceSn());
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::fetchMessageFromServerSmart licenseExceeded: " + dataManager.isLicenseExceeded());
        
        if(dataManager.isLicenseExceeded()) {
            HiLog.warn(LABEL_LOG, "许可证超限，跳过消息获取");
            return;
        }

        String finalTargetUrl = dataManager.getFetchMessageUrl() + "/receive?deviceSn=" + dataManager.getDeviceSn();
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::fetchMessageFromServerSmart finalTargetUrl: " + finalTargetUrl);

        // 智能检查网络条件
        if (!networkStateManager.shouldExecuteNetworkTask(getContext(), finalTargetUrl)) {
            HiLog.warn(LABEL_LOG, "网络条件不满足，跳过消息获取");
            return;
        }

        JSONObject response = fetchDataFromServerSmart(finalTargetUrl);
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::fetchMessageFromServerSmart response: " + response);

        if (response != null && response.getBoolean("success")) {
            try {
                JSONObject data = response.getJSONObject("data");
                if (data != null) {
                    // 记录消息统计信息
                    HiLog.info(LABEL_LOG, String.format("消息统计: 总数=%d, 个人消息=%d, 公共消息=%d, 部门数=%d", 
                        data.getInt("totalMessages"),
                        data.getInt("personalMessagesCount"),
                        data.getInt("publicMessagesCount"),
                        data.getJSONArray("departments").length()));

                    // 记录消息类型统计
                    JSONObject typeCount = data.getJSONObject("messageTypeCount");
                    Iterator<String> types = typeCount.keys();
                    while (types.hasNext()) {
                        String type = types.next();
                        HiLog.info(LABEL_LOG, String.format("消息类型[%s]数量: %d", 
                            type, typeCount.getInt(type)));
                    }

                    if (data.has("messages")) {
                        JSONArray messages = data.getJSONArray("messages");
                        for (int i = 0; i < messages.length(); i++) {
                            JSONObject message = messages.getJSONObject(i);
                            HiLog.info(LABEL_LOG, "处理消息: " + message.toString());

                            String messageType = message.getString("message_type");
                            String translatedMessageType = MESSAGE_TYPE_MAP.getOrDefault(messageType, messageType);
                            
                            // 构建消息内容
                            String messageContent = String.format("平台在%s%s：%s, 内容为:%s (部门: %s)",
                                message.getString("sent_time"),
                                message.isNull("user_name") || message.getString("user_name").isEmpty() ? "群发" : "发来",
                                translatedMessageType,
                                message.getString("message"),
                                message.getString("department_name"));

                            HiLog.info(LABEL_LOG, "消息内容: " + messageContent);
                            showNotification(messageContent);

                            // 构建响应消息
                            JSONObject responseMessage = new JSONObject();
                            // 复制原有字段
                            responseMessage.put("department_id", message.getString("department_id"));
                            responseMessage.put("department_name", message.getString("department_name"));
                            responseMessage.put("is_public", message.getBoolean("is_public"));
                            responseMessage.put("message", message.getString("message"));
                            responseMessage.put("message_id", message.getString("message_id"));
                            responseMessage.put("message_type", message.getString("message_type"));
                            responseMessage.put("sent_time", message.getString("sent_time"));
                            responseMessage.put("user_id", message.isNull("user_id") ? JSONObject.NULL : message.get("user_id"));
                            responseMessage.put("user_name", message.isNull("user_name") ? JSONObject.NULL : message.get("user_name"));
                            responseMessage.put("sender_type", "device");
                            responseMessage.put("receiver_type", "platform");
                            
                            // 更新需要修改的字段
                            responseMessage.put("device_sn", dataManager.getDeviceSn());
                            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
                            String formattedTime = Instant.now().atZone(ZoneId.of("Asia/Shanghai")).format(formatter);
                            responseMessage.put("received_time", formattedTime);
                            responseMessage.put("message_status", "responded");

                            // 智能发送响应消息
                            String responseUrl = dataManager.getFetchMessageUrl() + "/send";
                            HiLog.info(LABEL_LOG, "智能发送响应消息到: " + responseUrl);
                            sendMessagesToPlatformSmart(responseUrl, responseMessage.toString());
                        }
                    }
                }
            } catch (JSONException e) {
                HiLog.error(LABEL_LOG, "处理消息时发生错误: " + e.getMessage());
                e.printStackTrace();
            }
        }
    }

    /**
     * 智能从服务器获取数据 - 增强版
     */
    private JSONObject fetchDataFromServerSmart(String targetUrl) {
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::fetchDataFromServerSmart :: targetUrl: " + targetUrl);
        
        // 智能检查网络条件
        if (!networkStateManager.shouldExecuteNetworkTask(getContext(), targetUrl)) {
            HiLog.warn(LABEL_LOG, "网络条件不满足，跳过数据获取: " + targetUrl);
            return null;
        }
        
        JSONObject result = null;
        try {
            URL url = new URL(targetUrl);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(5000); // 5秒超时
            connection.setReadTimeout(5000); // 5秒超时
            connection.setRequestMethod("GET");
            connection.setRequestProperty("Accept", "application/json");

            int responseCode = connection.getResponseCode();
            HiLog.info(LABEL_LOG, "HttpServiceEnhanced::fetchDataFromServerSmart ::responseCode " + responseCode);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                try (InputStream is = connection.getInputStream();
                     ByteArrayOutputStream resultStream = new ByteArrayOutputStream()) {

                    byte[] buffer = new byte[1024];
                    int length;
                    while ((length = is.read(buffer)) != -1) {
                        resultStream.write(buffer, 0, length);
                    }

                    String response = resultStream.toString(StandardCharsets.UTF_8.name());
                    result = new JSONObject(response);
                }
            } else {
                HiLog.error(LABEL_LOG, "智能数据获取失败, response code: " + responseCode);
            }

            connection.disconnect();
        } catch (Exception e) {
            e.printStackTrace();
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::fetchDataFromServerSmart :: exception: " + e.getMessage());
        }
        return result;
    }

    /**
     * 智能发送消息到平台 - 增强版
     */
    public void sendMessagesToPlatformSmart(String httpUrl, String message) {
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::sendMessagesToPlatformSmart httpUrl: " + httpUrl);
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::sendMessagesToPlatformSmart message: " + message);
        
        if (networkStateManager.shouldExecuteNetworkTask(getContext(), httpUrl)) {
            HiLog.info(LABEL_LOG, "HttpServiceEnhanced::sendMessagesToPlatformSmart 智能发送消息: " + httpUrl);
            uploadDataSmart(httpUrl, message);
        } else {
            HiLog.warn(LABEL_LOG, "网络条件不满足，跳过消息发送: " + httpUrl);
        }
    }

    /**
     * 智能检查并重传缓存数据 - 增强版
     */
    private void checkAndRetryCachedDataSmart() {
        try {
            // 检查是否有缓存数据需要重传
            boolean hasHealthCache = !healthDataCache.isCacheEmpty(HealthDataCache.DataType.HEALTH_DATA);
            boolean hasDeviceCache = !healthDataCache.isCacheEmpty(HealthDataCache.DataType.DEVICE_INFO);
            boolean hasEventCache = !healthDataCache.isCacheEmpty(HealthDataCache.DataType.COMMON_EVENT);
            
            if (!hasHealthCache && !hasDeviceCache && !hasEventCache) {
                return; // 没有缓存数据，跳过
            }
            
            HiLog.info(LABEL_LOG, "HttpServiceEnhanced::checkAndRetryCachedDataSmart 检测到缓存数据，开始智能重传");
            healthDataCache.logCacheStatus();
            
            // 智能重传
            retryAllCachedDataSmart();
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::checkAndRetryCachedDataSmart error: " + e.getMessage());
        }
    }

    /**
     * 智能批量重传缓存数据 - 增强版
     */
    private void retryAllCachedDataSmart() {
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::retryAllCachedDataSmart 开始智能批量重传缓存数据");
        
        try {
            // 智能重传健康数据
            retryHealthDataSmart();
            
            // 智能重传设备信息
            retryCachedDataSmart(HealthDataCache.DataType.DEVICE_INFO, dataManager.getUploadDeviceInfoUrl());
            
            // 智能重传通用事件
            retryCachedDataSmart(HealthDataCache.DataType.COMMON_EVENT, dataManager.getUploadCommonEventUrl());
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HttpServiceEnhanced::retryAllCachedDataSmart error: " + e.getMessage());
        }
    }

    /**
     * 立即智能重传所有缓存数据 - 网络恢复时调用
     */
    private void retryAllCachedDataImmediate() {
        // 清除网络状态缓存，强制重新检测
        networkStateManager.clearCache();
        
        // 立即执行智能重传
        retryAllCachedDataSmart();
    }

    /**
     * 针对特定服务器重传数据
     */
    private void retryDataForServer(String serverUrl) {
        // 清除特定服务器的缓存状态
        networkStateManager.clearServerCache(serverUrl);
        
        // 根据服务器URL确定数据类型并重传
        if (serverUrl.equals(dataManager.getUploadHealthDataUrl())) {
            retryHealthDataSmart();
        } else if (serverUrl.equals(dataManager.getUploadDeviceInfoUrl())) {
            retryCachedDataSmart(HealthDataCache.DataType.DEVICE_INFO, serverUrl);
        } else if (serverUrl.equals(dataManager.getUploadCommonEventUrl())) {
            retryCachedDataSmart(HealthDataCache.DataType.COMMON_EVENT, serverUrl);
        }
    }

    /**
     * 智能健康数据重传 - 增强版
     */
    private void retryHealthDataSmart() {
        try {
            List<String> cachedHealthData = healthDataCache.getAllCachedData(HealthDataCache.DataType.HEALTH_DATA);
            if (cachedHealthData.isEmpty()) {
                return;
            }
            
            CustomLogger.info("HttpServiceEnhanced::retryHealthDataSmart", "开始智能重传健康数据，共 " + cachedHealthData.size() + " 条");
            
            // 检查网络条件
            if (!networkStateManager.shouldExecuteNetworkTask(getContext(), dataManager.getUploadHealthDataUrl())) {
                CustomLogger.warn("HttpServiceEnhanced::retryHealthDataSmart", "网络条件不满足，暂停健康数据重传");
                return;
            }
            
            // 使用现有的智能批量上传方法
            boolean success = uploadAllCachedDataSmart();
            if (success) {
                CustomLogger.info("HttpServiceEnhanced::retryHealthDataSmart", "健康数据智能重传成功");
            } else {
                CustomLogger.warn("HttpServiceEnhanced::retryHealthDataSmart", "健康数据智能重传失败");
            }
        } catch (Exception e) {
            CustomLogger.error("HttpServiceEnhanced::retryHealthDataSmart", "错误: " + e.getMessage());
        }
    }

    /**
     * 智能缓存数据重传 - 增强版
     */
    private void retryCachedDataSmart(HealthDataCache.DataType dataType, String url) {
        try {
            List<String> cachedData = healthDataCache.getAllCachedData(dataType);
            if (cachedData.isEmpty()) {
                return;
            }
            
            CustomLogger.info("HttpServiceEnhanced::retryCachedDataSmart", "[" + dataType.getDisplayName() + "] 开始智能重传 " + cachedData.size() + " 条缓存数据");
            
            // 检查网络条件
            if (!networkStateManager.shouldExecuteNetworkTask(getContext(), url)) {
                CustomLogger.warn("HttpServiceEnhanced::retryCachedDataSmart", "[" + dataType.getDisplayName() + "] 网络条件不满足，暂停重传");
                return;
            }
            
            int successCount = 0;
            for (int i = 0; i < cachedData.size(); i++) {
                String data = cachedData.get(i);
                
                // 记录详细日志
                if (dataType == HealthDataCache.DataType.DEVICE_INFO) {
                    CustomLogger.logDeviceInfo("智能重传第" + (i + 1) + "条设备信息", data);
                } else if (dataType == HealthDataCache.DataType.COMMON_EVENT) {
                    try {
                        JSONObject eventJson = new JSONObject(data);
                        String deviceInfo = eventJson.has("deviceInfo") ? eventJson.get("deviceInfo").toString() : null;
                        String healthInfo = eventJson.has("healthData") ? eventJson.get("healthData").toString() : null;
                        CustomLogger.logCommonEvent("智能重传第" + (i + 1) + "条通用事件", deviceInfo, healthInfo);
                    } catch (Exception e) {
                        CustomLogger.warn("HttpServiceEnhanced::retryCachedDataSmart", "解析通用事件数据失败: " + e.getMessage());
                    }
                }
                
                boolean success = uploadDataSmart(url, data);
                if (success) {
                    successCount++;
                } else {
                    break; // 如果某条失败，停止重传，保留后续数据
                }
            }
            
            if (successCount > 0) {
                if (successCount == cachedData.size()) {
                    // 全部成功，清空缓存
                    healthDataCache.clearCache(dataType);
                    CustomLogger.info("HttpServiceEnhanced::retryCachedDataSmart", "[" + dataType.getDisplayName() + "] 全部智能重传成功，缓存已清空");
                } else {
                    CustomLogger.info("HttpServiceEnhanced::retryCachedDataSmart", "[" + dataType.getDisplayName() + "] 部分智能重传成功: " + successCount + "/" + cachedData.size());
                }
            }
        } catch (Exception e) {
            CustomLogger.error("HttpServiceEnhanced::retryCachedDataSmart", "[" + dataType.getDisplayName() + "] 错误: " + e.getMessage());
        }
    }

    // 显示通知
    private void showNotification(String textContent) {
        NotificationRequest request = new NotificationRequest(notificationId++);
        NotificationRequest.NotificationNormalContent content = new NotificationRequest.NotificationNormalContent();
        content.setTitle(dataManager.getCustomerName())
                .setText(textContent);
        NotificationRequest.NotificationContent notificationContent = new NotificationRequest.NotificationContent(content);
        request.setContent(notificationContent);
        try {
            NotificationHelper.publishNotification(request);
            keepBackgroundRunning(notificationId, request);
            storeValue("notificationId", String.valueOf(notificationId));
        } catch (RemoteException ex) {
            ex.printStackTrace();
        }
    }

    // 获取Preferences的优化版
    private Preferences getPreferences() {
        if (preferences == null) {
            Context context = getContext();
            DatabaseHelper databaseHelper = new DatabaseHelper(context);
            String fileName = "pref";
            preferences = databaseHelper.getPreferences(fileName);
        }
        return preferences;
    }

    // 存储值到Preferences
    public void storeValue(String key, String value){
        Preferences preferences = getPreferences();
        preferences.putString(key, value);
        preferences.flush();
    }

    // 从Preferences获取值
    public String fetchValue(String key){
        Preferences preferences = getPreferences();
        return preferences.getString(key,"");
    }

    @Override
    public void onBackground() {
        super.onBackground();
        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::onBackground");
    }

    @Override
    public void onStop() {
        super.onStop();
        cancelBackgroundRunning();

        // 取消定时器
        if (masterHttpTimer != null) {
            masterHttpTimer.cancel();
        }
        
        // 移除网络状态监听器
        networkStateManager.removeNetworkStateChangeListener(this);

        HiLog.info(LABEL_LOG, "HttpServiceEnhanced::onStop");
    }

    @Override
    public void onCommand(Intent intent, boolean restart, int startId) {
    }

    @Override
    public IRemoteObject onConnect(Intent intent) {
        return null;
    }

    @Override
    public void onDisconnect(Intent intent) {
    }
}