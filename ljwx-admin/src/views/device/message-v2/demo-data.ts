// 用于演示的模拟数据
export const mockMessageV2Data = {
  // 模拟消息列表数据
  messageList: {
    records: [
      {
        id: 1,
        messageId: "MSG-2025091001",
        customerId: 1,
        orgId: 101,
        userId: "user001",
        deviceSn: "DEV20250101",
        title: "紧急健康告警",
        message: "检测到用户心率异常，请及时关注",
        messageType: "EMERGENCY",
        senderType: "SYSTEM",
        receiverType: "USER",
        urgency: "CRITICAL",
        messageStatus: "ACKNOWLEDGED",
        sentTime: "2025-09-10T10:30:00",
        receivedTime: "2025-09-10T10:30:15",
        acknowledgedTime: "2025-09-10T10:32:00",
        expiresAt: null,
        respondedNumber: 1,
        createTime: "2025-09-10T10:29:30",
        updateTime: "2025-09-10T10:32:00",
        createUser: "system",
        updateUser: "system",
        totalTargets: 3,
        deliveredCount: 3,
        acknowledgedCount: 3,
        failedCount: 0,
        pendingCount: 0,
        details: [
          {
            id: 1,
            messageId: 1,
            customerId: 1,
            targetId: "user001",
            targetType: "USER",
            channel: "DEVICE",
            deliveryStatus: "ACKNOWLEDGED",
            sentTime: "2025-09-10T10:30:00",
            deliveredTime: "2025-09-10T10:30:15",
            acknowledgedTime: "2025-09-10T10:32:00",
            responseData: { response: "已查看" },
            failureReason: null,
            retryCount: 0,
            createTime: "2025-09-10T10:30:00",
            updateTime: "2025-09-10T10:32:00"
          }
        ]
      },
      {
        id: 2,
        messageId: "MSG-2025091002",
        customerId: 1,
        orgId: 101,
        userId: "user002",
        deviceSn: "DEV20250102",
        title: "健康数据上传提醒",
        message: "您今日尚未同步健康数据，请及时上传",
        messageType: "NOTIFICATION",
        senderType: "SYSTEM",
        receiverType: "USER",
        urgency: "MEDIUM",
        messageStatus: "DELIVERED",
        sentTime: "2025-09-10T09:00:00",
        receivedTime: "2025-09-10T09:00:08",
        acknowledgedTime: null,
        expiresAt: "2025-09-10T23:59:59",
        respondedNumber: 0,
        createTime: "2025-09-10T08:59:45",
        updateTime: "2025-09-10T09:00:08",
        createUser: "system",
        updateUser: "system",
        totalTargets: 1,
        deliveredCount: 1,
        acknowledgedCount: 0,
        failedCount: 0,
        pendingCount: 0,
        details: [
          {
            id: 2,
            messageId: 2,
            customerId: 1,
            targetId: "user002",
            targetType: "USER",
            channel: "DEVICE",
            deliveryStatus: "DELIVERED",
            sentTime: "2025-09-10T09:00:00",
            deliveredTime: "2025-09-10T09:00:08",
            acknowledgedTime: null,
            responseData: null,
            failureReason: null,
            retryCount: 0,
            createTime: "2025-09-10T09:00:00",
            updateTime: "2025-09-10T09:00:08"
          }
        ]
      },
      {
        id: 3,
        messageId: "MSG-2025091003",
        customerId: 1,
        orgId: 102,
        userId: null,
        deviceSn: null,
        title: "部门健康报告",
        message: "研发部本月健康统计报告已生成，请查看",
        messageType: "INFO",
        senderType: "SYSTEM",
        receiverType: "GROUP",
        urgency: "LOW",
        messageStatus: "FAILED",
        sentTime: "2025-09-10T08:00:00",
        receivedTime: null,
        acknowledgedTime: null,
        expiresAt: null,
        respondedNumber: 0,
        createTime: "2025-09-10T07:59:30",
        updateTime: "2025-09-10T08:01:00",
        createUser: "admin",
        updateUser: "system",
        totalTargets: 15,
        deliveredCount: 10,
        acknowledgedCount: 8,
        failedCount: 5,
        pendingCount: 0,
        details: [
          {
            id: 3,
            messageId: 3,
            customerId: 1,
            targetId: "group_rd",
            targetType: "GROUP",
            channel: "EMAIL",
            deliveryStatus: "FAILED",
            sentTime: "2025-09-10T08:00:00",
            deliveredTime: null,
            acknowledgedTime: null,
            responseData: null,
            failureReason: "邮箱服务器连接超时",
            retryCount: 3,
            createTime: "2025-09-10T08:00:00",
            updateTime: "2025-09-10T08:01:00"
          }
        ]
      }
    ],
    total: 3,
    pages: 1,
    page: 1,
    pageSize: 20
  },

  // 模拟统计数据
  statisticsData: {
    totalMessages: 156,
    sentMessages: 148,
    receivedMessages: 142,
    acknowledgedMessages: 128,
    failedMessages: 14,
    expiredMessages: 2,
    pendingMessages: 8,
    sendSuccessRate: 94.9,
    receiveSuccessRate: 91.0,
    acknowledgeSuccessRate: 82.1,
    averageResponseTime: 45000,
    messageTypeStats: {
      "EMERGENCY": 8,
      "ALERT": 25,
      "WARNING": 18,
      "NOTIFICATION": 89,
      "INFO": 16
    },
    senderTypeStats: {
      "SYSTEM": 142,
      "USER": 8,
      "DEVICE": 4,
      "API": 2
    },
    receiverTypeStats: {
      "USER": 98,
      "DEVICE": 42,
      "GROUP": 16,
      "BROADCAST": 0
    },
    urgencyStats: {
      "CRITICAL": 12,
      "HIGH": 28,
      "MEDIUM": 75,
      "LOW": 41
    },
    messageStatusStats: {
      "DRAFT": 2,
      "PENDING": 8,
      "SENT": 6,
      "DELIVERED": 14,
      "ACKNOWLEDGED": 128,
      "FAILED": 14,
      "EXPIRED": 2
    },
    channelStats: {
      "DEVICE": 98,
      "SMS": 25,
      "EMAIL": 18,
      "PUSH": 12,
      "WECHAT": 3
    },
    orgStats: {
      "部门A": 45,
      "部门B": 38,
      "部门C": 42,
      "部门D": 31
    },
    deviceStats: {},
    dailyStats: {
      "2025-09-04": 18,
      "2025-09-05": 22,
      "2025-09-06": 19,
      "2025-09-07": 25,
      "2025-09-08": 28,
      "2025-09-09": 24,
      "2025-09-10": 20
    },
    hourlyStats: {}
  },

  // 模拟渠道统计数据
  channelStatistics: {
    "DEVICE": {
      totalMessages: 98,
      deliveredMessages: 94,
      acknowledgedMessages: 85,
      failedMessages: 4,
      averageDeliveryTime: 2500,
      successRate: 95.9
    },
    "SMS": {
      totalMessages: 25,
      deliveredMessages: 23,
      acknowledgedMessages: 20,
      failedMessages: 2,
      averageDeliveryTime: 8500,
      successRate: 92.0
    },
    "EMAIL": {
      totalMessages: 18,
      deliveredMessages: 15,
      acknowledgedMessages: 13,
      failedMessages: 3,
      averageDeliveryTime: 12000,
      successRate: 83.3
    },
    "PUSH": {
      totalMessages: 12,
      deliveredMessages: 10,
      acknowledgedMessages: 8,
      failedMessages: 2,
      averageDeliveryTime: 1500,
      successRate: 83.3
    },
    "WECHAT": {
      totalMessages: 3,
      deliveredMessages: 3,
      acknowledgedMessages: 2,
      failedMessages: 0,
      averageDeliveryTime: 3000,
      successRate: 100.0
    }
  },

  // 模拟消息汇总数据
  messageSummary: {
    messageId: 1,
    totalTargets: 3,
    distributionDetails: {
      pending: 0,
      sent: 0,
      delivered: 0,
      acknowledged: 3,
      failed: 0,
      expired: 0
    },
    channelBreakdown: {
      "DEVICE": {
        total: 3,
        delivered: 3,
        acknowledged: 3,
        failed: 0
      },
      "SMS": {
        total: 0,
        delivered: 0,
        acknowledged: 0,
        failed: 0
      },
      "EMAIL": {
        total: 0,
        delivered: 0,
        acknowledged: 0,
        failed: 0
      },
      "PUSH": {
        total: 0,
        delivered: 0,
        acknowledged: 0,
        failed: 0
      },
      "WECHAT": {
        total: 0,
        delivered: 0,
        acknowledged: 0,
        failed: 0
      }
    },
    averageDeliveryTime: 15000,
    averageAcknowledgmentTime: 105000,
    completionRate: 100.0,
    successRate: 100.0
  }
};

// 导出给组件使用的工具函数
export function getMockMessageList() {
  return Promise.resolve({
    error: null,
    data: mockMessageV2Data.messageList
  });
}

export function getMockStatistics() {
  return Promise.resolve({
    error: null,
    data: mockMessageV2Data.statisticsData
  });
}

export function getMockChannelStatistics() {
  return Promise.resolve({
    error: null,
    data: mockMessageV2Data.channelStatistics
  });
}

export function getMockMessageSummary(messageId: number) {
  return Promise.resolve({
    error: null,
    data: { ...mockMessageV2Data.messageSummary, messageId }
  });
}