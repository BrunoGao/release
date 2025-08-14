/**
 * 智能健康数据分析平台 - 常量定义
 */

console.log('📦 加载 constants.js');

// 告警类型映射
const ALERT_TYPE_MAP = {
    'WEAR_STATUS_CHANGED': '佩戴状态变化',
    'HEART_RATE_ABNORMAL': '心率异常',
    'BLOOD_OXYGEN_LOW': '血氧过低',
    'TEMPERATURE_HIGH': '体温过高',
    'FALL_DETECTED': '跌倒检测',
    'SOS_ALERT': 'SOS求救',
    'DEVICE_OFFLINE': '设备离线',
    'BATTERY_LOW': '电量不足',
    'GEOFENCE_EXIT': '电子围栏异常'
};

// 告警状态映射
const ALERT_STATUS_MAP = {
    'pending': '待处理',
    'processing': '处理中',
    'resolved': '已解决',
    'closed': '已关闭',
    'ignored': '已忽略',
    '0': '待处理',
    '1': '处理中',
    '2': '已解决',
    '3': '已关闭'
};

// 告警级别映射
const ALERT_LEVEL_MAP = {
    'critical': '严重',
    'high': '高级',
    'medium': '中级',
    'low': '低级',
    'info': '信息',
    '1': '严重',
    '2': '高级',
    '3': '中级',
    '4': '低级',
    '5': '信息'
};

// 消息类型映射
const MESSAGE_TYPE_MAP = {
    'system': '系统消息',
    'alert': '告警消息',
    'health': '健康提醒',
    'device': '设备通知',
    'maintenance': '维护通知',
    'user': '用户消息',
    'emergency': '紧急通知'
};

// 消息状态映射
const MESSAGE_STATUS_MAP = {
    'pending': '待处理',
    'read': '已读',
    'unread': '未读',
    'processed': '已处理',
    '0': '未读',
    '1': '待处理',
    '2': '已读',
    '3': '已处理'
};

// 告警类型颜色映射
const ALERT_TYPE_COLOR = {
    'WEAR_STATUS_CHANGED': '#00e4ff',
    'HEART_RATE_ABNORMAL': '#ff4444',
    'BLOOD_OXYGEN_LOW': '#ff6666',
    'TEMPERATURE_HIGH': '#ff8800',
    'FALL_DETECTED': '#ff0000',
    'SOS_ALERT': '#ff0000',
    'DEVICE_OFFLINE': '#ffbb00',
    'BATTERY_LOW': '#ffa500',
    'GEOFENCE_EXIT': '#ff6600'
};

// 告警级别颜色映射
const ALERT_SEVERITY_COLOR = {
    'critical': '#ff4444',
    'high': '#ff6666',
    'medium': '#ffbb00',
    'low': '#00ff9d',
    'info': '#7ecfff',
    '1': '#ff4444',
    '2': '#ff6666',
    '3': '#ffbb00',
    '4': '#00ff9d',
    '5': '#7ecfff'
};

// 告警状态颜色映射
const ALERT_STATUS_COLOR = {
    'pending': '#ffbb00',
    'processing': '#00e4ff',
    'resolved': '#00ff9d',
    'closed': '#666666',
    'ignored': '#999999',
    '0': '#ffbb00',
    '1': '#00e4ff',
    '2': '#00ff9d',
    '3': '#666666'
};

// 消息类型颜色映射
const MESSAGE_TYPE_COLOR = {
    'system': '#7ecfff',
    'alert': '#ff4444',
    'health': '#00ff9d',
    'device': '#00e4ff',
    'maintenance': '#ffbb00',
    'user': '#9d4edd',
    'emergency': '#ff0000'
}; 