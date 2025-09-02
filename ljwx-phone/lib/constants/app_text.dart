class AppText {
  // 通用
  static const String loading = '加载中...';
  static const String retry = '重试';
  static const String noData = '暂无数据';
  static const String error = '错误';
  static const String confirm = '确认';
  static const String cancel = '取消';
  static const String settings = '设置';
  static const String logout = '退出登录';
  static const String logoutConfirm = '确定要退出登录吗？';
  static const String backToHome = '返回首页';
  static const String viewMore = '查看更多';
  static const String seeAll = '查看全部';

  // 登录
  static const String login = '登录';
  static const String loginFailed = '登录失败';
  static const String phoneNumber = '手机号';
  static const String phone = '手机号';
  static const String status = '状态';
  static const String password = '密码';
  static const String enterPhoneNumber = '请输入手机号';
  static const String enterPassword = '请输入密码';
  static const String invalidPhoneNumber = '请输入有效的手机号';
  static const String invalidPassword = '密码长度不能小于6位';

  // 首页
  static const String healthMonitor = '健康监测';
  static const String userInfo = '用户信息';
  static const String healthData = '健康数据';
  static const String alerts = '告警信息';
  static const String messages = '消息通知';
  static const String deviceInfo = '设备信息';
  static const String noAlerts = '暂无告警信息';
  static const String noMessages = '暂无消息';
  static const String noDeviceInfo = '暂无设备信息';
  static const String employeeNumber = '员工号';
  static const String department = '部门';
  static const String deviceNumber = '设备号';
  static const String notSet = '未设置';
  static const String noDepartment = '未分配部门';
  static const String markAsRead = '标记已读';
  static const String delete = '删除';

  // 消息类型
  static const String messageJob = '作业指引';
  static const String messageTask = '任务管理';
  static const String messageAnnouncement = '公告';
  static const String messageNotification = '通知';
  static const String messagePending = '待处理';
  static const String messageResponded = '已响应';

  // 告警级别和类型
  static const String alertCritical = '紧急';
  static const String alertHigh = '重要';
  static const String alertMedium = '一般';
  static const String alertFallDown = '跌倒告警';
  static const String alertOneKeyAlarm = '一键告警';
  static const String alertSleep = '睡眠异常';
  static const String alertHeartRate = '心率告警';
  static const String alertBloodOxygen = '血氧告警';
  static const String alertTemperature = '体温告警';
  static const String alertBloodPressure = '血压告警';
  static const String alertActivity = '活动告警';
  static const String alertPending = '待处理';
  static const String alertResponded = '已处理';

  // 统计信息
  static const String statistics = '统计信息';

  // 设置页面
  static const String notificationSettings = '通知设置';
  static const String enableNotifications = '启用通知';
  static const String notificationDescription = '接收健康监测和告警通知';
  static const String displaySettings = '显示设置';
  static const String darkMode = '深色模式';
  static const String darkModeDescription = '使用深色主题';
  static const String language = '语言';
  static const String selectLanguage = '选择语言';
  static const String accountSettings = '账号设置';
  static const String changePassword = '修改密码';

  // 健康数据
  static const String heartRate = '心率';
  static const String bloodPressure = '血压';
  static const String temperature = '体温';
  static const String oxygenSaturation = '血氧';
  static const String respiratoryRate = '呼吸率';
  static const String heartRateUnit = '次/分';
  static const String bloodPressureUnit = 'mmHg';
  static const String temperatureUnit = '°C';
  static const String oxygenSaturationUnit = '%';
  static const String respiratoryRateUnit = '次/分';
  static const String stress = '压力';
  // 用户信息
  static const String userName = '用户名';
  static const String userCardNumber = '工号';
  static const String deviceStatus = '设备状态';
  static const String chargingStatus = '充电状态';
  static const String wearableStatus = '佩戴状态';
  static const String createTime = '创建时间';
  static const String updateTime = '更新时间';
  static const String position = '职位';
  static const String workingYears = '工作年限';
  static const String deviceSn = '设备序列号';

  // 健康数据
  static const String bloodOxygen = '血氧';
  static const String steps = '步数';
  static const String distance = '距离';
  static const String calories = '卡路里';
  static const String lastCheckTime = '上次检测时间';

  // 告警信息
  static String totalAlerts(int count) => '共 $count 条告警';

  // 设备信息
  static const String deviceName = '设备名称';
  static const String deviceType = '设备类型';
  static const String deviceVersion = '设备版本';
  static const String bluetoothAddress = '蓝牙地址';
  static const String deviceStatusActive = '正常';
  static const String deviceStatusInactive = '异常';
  static const String deviceStatusCharging = '充电中';
  static const String deviceStatusNotCharging = '未充电';
  static const String deviceStatusWearing = '佩戴中';
  static const String deviceStatusNotWearing = '未佩戴';
  static const String batteryLevel = '电池电量';
  // 设备状态翻译
  static String translateDeviceStatus(String status) {
    switch (status) {
      case 'ACTIVE':
        return deviceStatusActive;
      case 'INACTIVE':
        return deviceStatusInactive;
      case 'CHARGING':
        return deviceStatusCharging;
      case 'NOT_CHARGING':
        return deviceStatusNotCharging;
      case 'NOT_WORN':
        return deviceStatusNotWearing;
      case 'WORN':
        return deviceStatusWearing;
      default:
        return status;
    }
  }

  // 消息状态翻译
  static String translateMessageStatus(String status) {
    switch (status) {
      case '1':
        return messagePending;
      case '2':
        return messageResponded;
      default:
        return status;
    }
  }

  // 消息类型翻译
  static String translateMessageType(String type) {
    switch (type) {
      case 'job':
        return messageJob;
      case 'task':
        return messageTask;
      case 'announcement':
        return messageAnnouncement;
      case 'notification':
        return messageNotification;
      default:
        return type;
    }
  }

  // 告警级别翻译
  static String translateAlertLevel(String level) {
    switch (level) {
      case 'critical':
        return alertCritical;
      case 'high':
        return alertHigh;
      case 'medium':
        return alertMedium;
      default:
        return level;
    }
  }

  // 告警状态翻译
  static String translateAlertStatus(String status) {
    switch (status) {
      case 'pending':
        return alertPending;
      case 'responded':
        return alertResponded;
      default:
        return status;
    }
  }

  // 告警类型翻译
  static String translateAlertType(String type) {
    switch (type) {
      case 'fall_down':
        return alertFallDown;
      case 'one_key_alarm':
        return alertOneKeyAlarm;
      case 'sleep':
        return alertSleep;
      case 'heart_rate':
        return alertHeartRate;
      case 'blood_oxygen':
        return alertBloodOxygen;
      case 'temperature':
        return alertTemperature;
      case 'blood_pressure':
        return alertBloodPressure;
      case 'activity':
        return alertActivity;
      default:
        return type;
    }
  }
} 