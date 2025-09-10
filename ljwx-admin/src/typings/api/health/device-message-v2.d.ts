declare namespace Api {
  namespace Health {
    // =============== V2 消息基础类型 ===============
    
    /** V2消息状态枚举 */
    type MessageStatusV2 = 'DRAFT' | 'PENDING' | 'SENT' | 'DELIVERED' | 'ACKNOWLEDGED' | 'FAILED' | 'EXPIRED';
    
    /** V2消息类型枚举 */
    type MessageTypeV2 = 'NOTIFICATION' | 'ALERT' | 'WARNING' | 'INFO' | 'EMERGENCY';
    
    /** V2发送者类型枚举 */
    type SenderTypeV2 = 'SYSTEM' | 'USER' | 'DEVICE' | 'API';
    
    /** V2接收者类型枚举 */
    type ReceiverTypeV2 = 'USER' | 'DEVICE' | 'GROUP' | 'BROADCAST';
    
    /** V2紧急程度枚举 */
    type UrgencyV2 = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    
    /** V2分发状态枚举 */
    type DeliveryStatusV2 = 'PENDING' | 'SENT' | 'DELIVERED' | 'ACKNOWLEDGED' | 'FAILED' | 'EXPIRED';
    
    /** V2分发渠道枚举 */
    type ChannelV2 = 'DEVICE' | 'SMS' | 'EMAIL' | 'PUSH' | 'WECHAT';
    
    /** V2目标类型枚举 */
    type TargetTypeV2 = 'DEVICE' | 'USER' | 'GROUP';
    
    // =============== V2 消息实体类型 ===============
    
    /** V2设备消息主表 */
    type DeviceMessageV2 = Common.CommonRecord<{
      messageId: string;
      customerId: number;
      orgId?: number;
      userId?: string;
      deviceSn?: string;
      title: string;
      message: string;
      messageType: MessageTypeV2;
      senderType: SenderTypeV2;
      receiverType: ReceiverTypeV2;
      urgency: UrgencyV2;
      messageStatus: MessageStatusV2;
      sentTime?: string;
      receivedTime?: string;
      acknowledgedTime?: string;
      expiresAt?: string;
      respondedNumber: number;
      createUser?: string;
      updateUser?: string;
    }>;
    
    /** V2设备消息详情表 */
    type DeviceMessageDetailV2 = Common.CommonRecord<{
      messageId: number;
      customerId: number;
      targetId: string;
      targetType: TargetTypeV2;
      channel: ChannelV2;
      deliveryStatus: DeliveryStatusV2;
      sentTime?: string;
      deliveredTime?: string;
      acknowledgedTime?: string;
      responseData?: any;
      failureReason?: string;
      retryCount: number;
    }>;
    
    /** V2消息详情（包含分发信息） */
    type DeviceMessageV2Detail = DeviceMessageV2 & {
      details: DeviceMessageDetailV2[];
      totalTargets: number;
      deliveredCount: number;
      acknowledgedCount: number;
      failedCount: number;
      pendingCount: number;
    };
    
    // =============== V2 查询和操作参数 ===============
    
    /** V2消息搜索参数 */
    type DeviceMessageV2SearchParams = CommonType.RecordNullable<
      Pick<DeviceMessageV2, 'customerId' | 'orgId' | 'userId' | 'deviceSn' | 'messageType' | 'senderType' | 'receiverType' | 'messageStatus' | 'urgency'> & 
      Api.Common.CommonSearchParams & {
        startTime?: string;
        endTime?: string;
        keyword?: string;
      }
    >;
    
    /** V2消息创建参数 */
    type DeviceMessageV2Create = Pick<
      DeviceMessageV2,
      | 'customerId'
      | 'orgId'
      | 'userId'
      | 'deviceSn'
      | 'title'
      | 'message'
      | 'messageType'
      | 'senderType'
      | 'receiverType'
      | 'urgency'
      | 'expiresAt'
    > & {
      targets?: Array<{
        targetId: string;
        targetType: TargetTypeV2;
        channel?: ChannelV2;
      }>;
    };
    
    /** V2消息更新参数 */
    type DeviceMessageV2Update = Partial<Pick<
      DeviceMessageV2,
      | 'title'
      | 'message'
      | 'messageType'
      | 'urgency'
      | 'messageStatus'
      | 'expiresAt'
    >>;
    
    /** V2消息确认参数 */
    type MessageAckV2 = {
      targetId: string;
      channel: string;
      responseData?: any;
    };
    
    /** V2批量消息确认参数 */
    type MessageBatchAck = {
      message_id: number;
      target_id: string;
      channel: string;
    };
    
    // =============== V2 统计分析类型 ===============
    
    /** V2消息统计信息 */
    type MessageStatisticsV2 = {
      totalMessages: number;
      sentMessages: number;
      receivedMessages: number;
      acknowledgedMessages: number;
      failedMessages: number;
      expiredMessages: number;
      pendingMessages: number;
      sendSuccessRate: number;
      receiveSuccessRate: number;
      acknowledgeSuccessRate: number;
      averageResponseTime: number;
      messageTypeStats: Record<string, number>;
      senderTypeStats: Record<string, number>;
      receiverTypeStats: Record<string, number>;
      urgencyStats: Record<string, number>;
      messageStatusStats: Record<string, number>;
      channelStats: Record<string, number>;
      orgStats: Record<string, number>;
      deviceStats: Record<string, number>;
      dailyStats: Record<string, number>;
      hourlyStats: Record<string, number>;
    };
    
    /** V2消息汇总信息 */
    type MessageSummaryV2 = {
      messageId: number;
      totalTargets: number;
      distributionDetails: {
        pending: number;
        sent: number;
        delivered: number;
        acknowledged: number;
        failed: number;
        expired: number;
      };
      channelBreakdown: Record<ChannelV2, {
        total: number;
        delivered: number;
        acknowledged: number;
        failed: number;
      }>;
      averageDeliveryTime: number;
      averageAcknowledgmentTime: number;
      completionRate: number;
      successRate: number;
    };
    
    /** V2渠道统计 */
    type ChannelStatisticsV2 = Record<ChannelV2, {
      totalMessages: number;
      deliveredMessages: number;
      acknowledgedMessages: number;
      failedMessages: number;
      averageDeliveryTime: number;
      successRate: number;
    }>;
    
    /** V2响应时间统计 */
    type ResponseTimeStatisticsV2 = {
      overall: {
        averageDeliveryTime: number;
        averageAcknowledgmentTime: number;
        p50DeliveryTime: number;
        p90DeliveryTime: number;
        p99DeliveryTime: number;
      };
      byMessageType: Record<MessageTypeV2, {
        averageDeliveryTime: number;
        averageAcknowledgmentTime: number;
      }>;
      byUrgency: Record<UrgencyV2, {
        averageDeliveryTime: number;
        averageAcknowledgmentTime: number;
      }>;
    };
    
    // =============== V2 列表返回类型 ===============
    
    /** V2消息列表 */
    type DeviceMessageV2List = Common.PaginatingQueryRecord<DeviceMessageV2Detail>;
    
    // =============== V2 消息生命周期追踪 ===============
    
    /** 消息生命周期阶段 */
    type MessageLifecycleStage = {
      stage: 'CREATED' | 'SENT' | 'DELIVERED' | 'ACKNOWLEDGED' | 'FAILED' | 'EXPIRED';
      timestamp: string;
      duration?: number; // 毫秒
      details?: any;
    };
    
    /** 消息生命周期追踪 */
    type MessageLifecycleTrace = {
      messageId: number;
      totalDuration: number; // 总耗时（毫秒）
      stages: MessageLifecycleStage[];
      currentStage: MessageLifecycleStage['stage'];
      isCompleted: boolean;
      success: boolean;
    };
    
    // =============== V2 实时状态更新 ===============
    
    /** 实时状态更新事件 */
    type MessageStatusUpdateEvent = {
      messageId: number;
      targetId: string;
      oldStatus: DeliveryStatusV2;
      newStatus: DeliveryStatusV2;
      timestamp: string;
      channel: ChannelV2;
      details?: any;
    };
    
    /** 实时统计更新事件 */
    type MessageStatisticsUpdateEvent = {
      customerId: number;
      orgId?: number;
      increment: Partial<MessageStatisticsV2>;
      timestamp: string;
    };
  }
}