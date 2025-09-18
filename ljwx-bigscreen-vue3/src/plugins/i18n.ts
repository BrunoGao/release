// 国际化配置 - i18n Configuration
import { createI18n } from 'vue-i18n'

// 中文语言包
const zh = {
  common: {
    confirm: '确认',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    search: '搜索',
    reset: '重置',
    submit: '提交',
    back: '返回',
    next: '下一步',
    prev: '上一步',
    loading: '加载中...',
    noData: '暂无数据',
    success: '操作成功',
    error: '操作失败',
    warning: '警告',
    info: '提示'
  },
  nav: {
    dashboard: '仪表盘',
    health: '健康监测',
    device: '设备管理',
    data: '数据分析',
    alert: '告警中心',
    system: '系统设置',
    profile: '个人资料',
    logout: '退出登录'
  },
  health: {
    profile: '健康档案',
    score: '健康评分',
    prediction: '健康预测',
    recommendation: '健康建议',
    trend: '趋势分析',
    report: '健康报告',
    heartRate: '心率',
    bloodPressure: '血压',
    temperature: '体温',
    bloodOxygen: '血氧',
    sleep: '睡眠',
    steps: '步数',
    calories: '卡路里',
    distance: '距离'
  },
  device: {
    status: '设备状态',
    online: '在线',
    offline: '离线',
    warning: '警告',
    error: '故障',
    lastSeen: '最后上线',
    battery: '电量',
    signal: '信号强度',
    location: '位置信息'
  },
  alert: {
    level: {
      info: '信息',
      warning: '警告', 
      error: '错误',
      critical: '严重'
    },
    status: {
      new: '新告警',
      processing: '处理中',
      resolved: '已解决',
      closed: '已关闭'
    }
  },
  time: {
    now: '刚刚',
    minuteAgo: '{n}分钟前',
    hourAgo: '{n}小时前',
    dayAgo: '{n}天前',
    weekAgo: '{n}周前',
    monthAgo: '{n}月前',
    yearAgo: '{n}年前',
    today: '今天',
    yesterday: '昨天',
    thisWeek: '本周',
    thisMonth: '本月',
    thisYear: '今年'
  },
  validation: {
    required: '{field}不能为空',
    email: '请输入有效的邮箱地址',
    phone: '请输入有效的手机号码',
    password: '密码长度至少为6位',
    confirm: '两次输入的密码不一致',
    min: '{field}长度不能少于{min}位',
    max: '{field}长度不能超过{max}位'
  }
}

// 英文语言包
const en = {
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    search: 'Search',
    reset: 'Reset',
    submit: 'Submit',
    back: 'Back',
    next: 'Next',
    prev: 'Previous',
    loading: 'Loading...',
    noData: 'No Data',
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info'
  },
  nav: {
    dashboard: 'Dashboard',
    health: 'Health Monitor',
    device: 'Device Management',
    data: 'Data Analysis',
    alert: 'Alert Center',
    system: 'System Settings',
    profile: 'Profile',
    logout: 'Logout'
  },
  health: {
    profile: 'Health Profile',
    score: 'Health Score',
    prediction: 'Health Prediction',
    recommendation: 'Recommendations',
    trend: 'Trend Analysis',
    report: 'Health Report',
    heartRate: 'Heart Rate',
    bloodPressure: 'Blood Pressure',
    temperature: 'Temperature',
    bloodOxygen: 'Blood Oxygen',
    sleep: 'Sleep',
    steps: 'Steps',
    calories: 'Calories',
    distance: 'Distance'
  },
  device: {
    status: 'Device Status',
    online: 'Online',
    offline: 'Offline',
    warning: 'Warning',
    error: 'Error',
    lastSeen: 'Last Seen',
    battery: 'Battery',
    signal: 'Signal Strength',
    location: 'Location'
  },
  alert: {
    level: {
      info: 'Info',
      warning: 'Warning',
      error: 'Error',
      critical: 'Critical'
    },
    status: {
      new: 'New',
      processing: 'Processing',
      resolved: 'Resolved',
      closed: 'Closed'
    }
  },
  time: {
    now: 'Just now',
    minuteAgo: '{n} minute(s) ago',
    hourAgo: '{n} hour(s) ago',
    dayAgo: '{n} day(s) ago',
    weekAgo: '{n} week(s) ago',
    monthAgo: '{n} month(s) ago',
    yearAgo: '{n} year(s) ago',
    today: 'Today',
    yesterday: 'Yesterday',
    thisWeek: 'This Week',
    thisMonth: 'This Month',
    thisYear: 'This Year'
  },
  validation: {
    required: '{field} is required',
    email: 'Please enter a valid email address',
    phone: 'Please enter a valid phone number',
    password: 'Password must be at least 6 characters',
    confirm: 'Password confirmation does not match',
    min: '{field} must be at least {min} characters',
    max: '{field} cannot exceed {max} characters'
  }
}

// 创建 i18n 实例
const i18n = createI18n({
  locale: 'zh', // 默认语言
  fallbackLocale: 'en', // 回退语言
  messages: {
    zh,
    en
  },
  // 启用组合式 API
  legacy: false,
  // 全局注入 $t
  globalInjection: true,
  // 缺少翻译时显示警告
  missingWarn: process.env.NODE_ENV === 'development',
  fallbackWarn: process.env.NODE_ENV === 'development'
})

// 语言切换函数
export const setLocale = (locale: string) => {
  if (i18n.global.availableLocales.includes(locale)) {
    i18n.global.locale.value = locale as any
    // 保存到本地存储
    localStorage.setItem('language', locale)
    // 更新 HTML lang 属性
    document.documentElement.lang = locale
  }
}

// 获取当前语言
export const getLocale = () => {
  return i18n.global.locale.value
}

// 从本地存储恢复语言设置
export const restoreLocale = () => {
  const savedLocale = localStorage.getItem('language')
  if (savedLocale && i18n.global.availableLocales.includes(savedLocale)) {
    setLocale(savedLocale)
  }
}

// 格式化相对时间
export const formatRelativeTime = (date: Date | string | number) => {
  const now = new Date()
  const target = new Date(date)
  const diff = now.getTime() - target.getTime()
  
  const minute = 60 * 1000
  const hour = minute * 60
  const day = hour * 24
  const week = day * 7
  const month = day * 30
  const year = day * 365
  
  const { t } = i18n.global
  
  if (diff < minute) {
    return t('time.now')
  } else if (diff < hour) {
    return t('time.minuteAgo', { n: Math.floor(diff / minute) })
  } else if (diff < day) {
    return t('time.hourAgo', { n: Math.floor(diff / hour) })
  } else if (diff < week) {
    return t('time.dayAgo', { n: Math.floor(diff / day) })
  } else if (diff < month) {
    return t('time.weekAgo', { n: Math.floor(diff / week) })
  } else if (diff < year) {
    return t('time.monthAgo', { n: Math.floor(diff / month) })
  } else {
    return t('time.yearAgo', { n: Math.floor(diff / year) })
  }
}

// 导出 i18n 实例
export default i18n