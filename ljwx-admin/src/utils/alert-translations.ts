/**
 * 告警相关的中文翻译工具
 * 统一管理告警类型、状态、严重级别的中英文映射
 */

// 告警类型中英文映射
export const alertTypeTranslations = {
  // 数据库中的英文告警类型 (来自 t_alert_rules 表)
  HEARTRATE_HIGH_ALERT: '心率过高告警',
  HEARTRATE_LOW_ALERT: '心率过低告警', 
  BLOOD_PRESSURE_HIGH_ALERT: '血压过高告警',
  BLOOD_PRESSURE_LOW_ALERT: '血压过低告警',
  TEMPERATURE_HIGH_ALERT: '体温过高告警',
  BLOOD_OXYGEN_LOW: '血氧过低',
  BLOOD_OXYGEN_LOW_ALERT: '血氧过低告警',
  PRESSURE_HIGH_ALERT: '压力过高告警',
  SLEEP_QUALITY_ALERT: '睡眠质量告警',
  FALLDOWN_EVENT: '跌倒事件',
  ONE_KEY_ALARM: '一键告警',
  SOS_EVENT: 'SOS紧急求助',
  COMMON_EVENT: '常规事件',
  custom: '自定义告警',
  metric: '指标告警',
  // 兼容旧的英文格式
  'Heartrate Low': '心率过低',
  'Heartrate High': '心率过高',
  'Blood Pressure Low': '血压过低',
  'Blood Pressure High': '血压过高',
  'Temperature Low': '体温过低',
  'Temperature High': '体温过高',
  'Blood Oxygen Low': '血氧过低',
  'Blood Oxygen High': '血氧过高',
  'Stress High': '压力过高',
  'Step Low': '步数不足',
  'Location Alert': '位置告警',
  'Device Offline': '设备离线',
  'Data Abnormal': '数据异常',
  // 兼容旧的中文字段
  heart_rate: '心率异常',
  blood_pressure: '血压异常',
  temperature: '体温异常',
  blood_oxygen: '血氧异常',
  stress: '压力异常',
  sleep: '睡眠异常',
  fall_down: '跌倒告警',
  one_key_alarm: '一键告警',
  作业指引消息: '作业指引',
  任务管理消息: '任务管理',
  公告消息: '公告'
} as const;

// 告警类型颜色映射
export const alertTypeColors = {
  // 数据库中的英文告警类型颜色
  HEARTRATE_HIGH_ALERT: '#e74c3c',
  HEARTRATE_LOW_ALERT: '#c0392b',
  BLOOD_PRESSURE_HIGH_ALERT: '#9b59b6',
  BLOOD_PRESSURE_LOW_ALERT: '#8e44ad',
  TEMPERATURE_HIGH_ALERT: '#f39c12',
  BLOOD_OXYGEN_LOW: '#3498db',
  BLOOD_OXYGEN_LOW_ALERT: '#2980b9',
  PRESSURE_HIGH_ALERT: '#e67e22',
  SLEEP_QUALITY_ALERT: '#2c3e50',
  FALLDOWN_EVENT: '#c0392b',
  ONE_KEY_ALARM: '#8e44ad',
  SOS_EVENT: '#e74c3c',
  COMMON_EVENT: '#95a5a6',
  custom: '#34495e',
  metric: '#16a085',
  // 兼容旧的英文格式颜色
  'Heartrate Low': '#ff4d4f',
  'Heartrate High': '#ff7875',
  'Blood Pressure Low': '#faad14',
  'Blood Pressure High': '#fa8c16',
  'Temperature Low': '#1890ff',
  'Temperature High': '#ff4d4f',
  'Blood Oxygen Low': '#722ed1',
  'Blood Oxygen High': '#9254de',
  'Stress High': '#f5222d',
  'Step Low': '#52c41a',
  'Location Alert': '#13c2c2',
  'Device Offline': '#666',
  'Data Abnormal': '#fa541c',
  // 兼容旧的中文字段颜色
  heart_rate: '#e74c3c',
  blood_pressure: '#9b59b6',
  temperature: '#f39c12',
  blood_oxygen: '#3498db',
  stress: '#e67e22',
  sleep: '#2c3e50',
  fall_down: '#c0392b',
  one_key_alarm: '#8e44ad',
  作业指引消息: '#27ae60',
  任务管理消息: '#27ae60',
  公告消息: '#f1c40f'
} as const;

// 告警状态中英文映射
export const alertStatusTranslations = {
  pending: '待处理',
  processing: '处理中',
  responded: '已响应',
  resolved: '已解决',
  closed: '已关闭'
} as const;

// 严重级别中英文映射
export const severityLevelTranslations = {
  critical: '严重',
  high: '高危',
  medium: '中等',
  low: '低危',
  '1': '低级',
  '2': '中级'
} as const;

// 严重级别颜色映射
export const severityLevelColors = {
  critical: '#e74c3c',
  high: '#e67e22',
  medium: '#f1c40f',
  low: '#3498db',
  '1': '#27ae60',
  '2': '#f39c12'
} as const;

// 告警优先级排序
export const alertTypePriority = {
  SOS_EVENT: 1,
  ONE_KEY_ALARM: 2,
  FALLDOWN_EVENT: 3,
  HEARTRATE_HIGH_ALERT: 4,
  HEARTRATE_LOW_ALERT: 5,
  BLOOD_PRESSURE_HIGH_ALERT: 6,
  BLOOD_PRESSURE_LOW_ALERT: 7,
  TEMPERATURE_HIGH_ALERT: 8,
  BLOOD_OXYGEN_LOW_ALERT: 9,
  BLOOD_OXYGEN_LOW: 10,
  PRESSURE_HIGH_ALERT: 11,
  SLEEP_QUALITY_ALERT: 12,
  COMMON_EVENT: 13,
  custom: 14,
  metric: 15,
  // 兼容旧字段
  one_key_alarm: 2,
  fall_down: 3,
  heart_rate: 4,
  blood_pressure: 6,
  sleep: 12
} as const;

/**
 * 获取告警类型的中文翻译
 * @param alertType 英文告警类型
 * @returns 中文翻译，如果没有找到则返回原值
 */
export function getAlertTypeTranslation(alertType: string): string {
  return alertTypeTranslations[alertType as keyof typeof alertTypeTranslations] || alertType;
}

/**
 * 获取告警类型的颜色
 * @param alertType 英文告警类型
 * @returns 颜色值
 */
export function getAlertTypeColor(alertType: string): string {
  return alertTypeColors[alertType as keyof typeof alertTypeColors] || '#666';
}

/**
 * 获取告警状态的中文翻译
 * @param status 英文状态
 * @returns 中文翻译，如果没有找到则返回原值
 */
export function getAlertStatusTranslation(status: string): string {
  return alertStatusTranslations[status as keyof typeof alertStatusTranslations] || status;
}

/**
 * 获取严重级别的中文翻译
 * @param level 英文级别
 * @returns 中文翻译，如果没有找到则返回原值
 */
export function getSeverityLevelTranslation(level: string): string {
  return severityLevelTranslations[level as keyof typeof severityLevelTranslations] || level;
}

/**
 * 获取严重级别的颜色
 * @param level 英文级别
 * @returns 颜色值
 */
export function getSeverityLevelColor(level: string): string {
  return severityLevelColors[level as keyof typeof severityLevelColors] || '#666';
}

/**
 * 获取告警类型的优先级
 * @param alertType 告警类型
 * @returns 优先级数字，越小优先级越高
 */
export function getAlertTypePriority(alertType: string): number {
  return alertTypePriority[alertType as keyof typeof alertTypePriority] || 99;
}