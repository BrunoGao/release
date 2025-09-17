import { request } from '@/service/request';

// =============== V2 Message API ===============

/** 获取V2消息列表 */
export function fetchGetDeviceMessageV2List(params?: Api.Health.DeviceMessageV2SearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.DeviceMessageV2List>({
    url: '/api/v2/messages',
    method: 'GET',
    params: filteredParams
  });
}

/** 创建V2消息 */
export function fetchCreateDeviceMessageV2(data: Api.Health.DeviceMessageV2Create) {
  return request<number>({
    url: '/api/v2/messages',
    method: 'POST',
    data
  });
}

/** 批量创建V2消息 */
export function fetchBatchCreateDeviceMessageV2(data: Api.Health.DeviceMessageV2Create[]) {
  return request<number[]>({
    url: '/api/v2/messages/batch',
    method: 'POST',
    data
  });
}

/** 更新V2消息 */
export function fetchUpdateDeviceMessageV2(messageId: number, data: Api.Health.DeviceMessageV2Update) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}`,
    method: 'PUT',
    data
  });
}

/** 删除V2消息 */
export function fetchDeleteDeviceMessageV2(messageId: number) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}`,
    method: 'DELETE'
  });
}

/** 批量删除V2消息 */
export function fetchBatchDeleteDeviceMessageV2(messageIds: number[]) {
  return request<boolean>({
    url: '/api/v2/messages/batch',
    method: 'DELETE',
    data: messageIds
  });
}

/** 获取V2消息详情 */
export function fetchGetDeviceMessageV2Detail(messageId: number) {
  return request<Api.Health.DeviceMessageV2Detail>({
    url: `/api/v2/messages/${messageId}`,
    method: 'GET'
  });
}

/** 发送消息到设备 */
export function fetchSendMessageToDevice(messageId: number, deviceSn: string) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}/send-to-device`,
    method: 'POST',
    params: { deviceSn }
  });
}

/** 发送消息到用户 */
export function fetchSendMessageToUser(messageId: number, userId: string) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}/send-to-user`,
    method: 'POST',
    params: { userId }
  });
}

/** 发送消息到部门 */
export function fetchSendMessageToDepartment(messageId: number, orgId: number) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}/send-to-department`,
    method: 'POST',
    params: { orgId }
  });
}

/** 批量分发消息 */
export function fetchBatchDistributeMessage(messageId: number, targets: string[], targetType: string) {
  return request<Api.Common.ResponseResult<any>>({
    url: `/api/v2/messages/${messageId}/batch-distribute`,
    method: 'POST',
    data: targets,
    params: { targetType }
  });
}

/** 确认消息 */
export function fetchAcknowledgeMessage(messageId: number, ackData: Api.Health.MessageAckV2) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}/acknowledge`,
    method: 'POST',
    data: ackData
  });
}

/** 批量确认消息 */
export function fetchBatchAcknowledgeMessages(requests: Api.Health.MessageBatchAck[]) {
  return request<boolean>({
    url: '/api/v2/messages/batch-acknowledge',
    method: 'POST',
    data: { requests }
  });
}

/** 标记消息为已送达 */
export function fetchMarkMessageAsDelivered(messageId: number, targetId: string, channel?: string) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}/mark-delivered`,
    method: 'POST',
    params: { targetId, channel }
  });
}

/** 重发失败消息 */
export function fetchRetryFailedMessage(messageId: number, targetId: string) {
  return request<boolean>({
    url: `/api/v2/messages/${messageId}/retry`,
    method: 'POST',
    params: { targetId }
  });
}

/** 获取设备消息 */
export function fetchGetMessagesByDevice(deviceSn: string, limit: number = 50) {
  return request<Api.Health.DeviceMessageV2Detail[]>({
    url: `/api/v2/messages/device/${deviceSn}`,
    method: 'GET',
    params: { limit }
  });
}

/** 获取用户消息 */
export function fetchGetMessagesByUser(userId: string, limit: number = 50) {
  return request<Api.Health.DeviceMessageV2Detail[]>({
    url: `/api/v2/messages/user/${userId}`,
    method: 'GET',
    params: { limit }
  });
}

/** 获取组织消息 */
export function fetchGetOrganizationMessages(customerId: number, orgId?: number, params?: Api.Common.CommonSearchParams) {
  return request<Api.Health.DeviceMessageV2List>({
    url: `/api/v2/messages/organization/${customerId}`,
    method: 'GET',
    params: { orgId, ...params }
  });
}

/** 获取未读消息数量 */
export function fetchGetUnreadCount(targetId: string, targetType: string) {
  return request<number>({
    url: '/api/v2/messages/unread-count',
    method: 'GET',
    params: { targetId, targetType }
  });
}

// =============== 统计分析API ===============

/** 获取消息统计信息 */
export function fetchGetMessageStatistics(params?: { customerId?: number; orgId?: number; startTime?: string; endTime?: string }) {
  return request<Api.Health.MessageStatisticsV2>({
    url: '/api/v2/messages/statistics',
    method: 'GET',
    params
  });
}

/** 获取消息汇总信息 */
export function fetchGetMessageSummary(messageId: number) {
  return request<Api.Health.MessageSummaryV2>({
    url: `/api/v2/messages/${messageId}/summary`,
    method: 'GET'
  });
}

/** 获取渠道分发统计 */
export function fetchGetChannelStatistics(params?: { customerId?: number; startTime?: string; endTime?: string }) {
  return request<Api.Common.ResponseResult<any>>({
    url: '/api/v2/messages/channel-statistics',
    method: 'GET',
    params
  });
}

/** 获取响应时间统计 */
export function fetchGetResponseTimeStatistics(params?: { customerId?: number; messageType?: string; startTime?: string; endTime?: string }) {
  return request<Api.Common.ResponseResult<any>>({
    url: '/api/v2/messages/response-time-statistics',
    method: 'GET',
    params
  });
}

/** 获取消息类型分布 */
export function fetchGetMessageTypeDistribution(params?: { customerId?: number; startTime?: string; endTime?: string }) {
  return request<Record<string, number>>({
    url: '/api/v2/messages/type-distribution',
    method: 'GET',
    params
  });
}

// =============== 管理API ===============

/** 清理过期消息 */
export function fetchCleanupExpiredMessages(before: string) {
  return request<number>({
    url: '/api/v2/messages/cleanup/expired',
    method: 'DELETE',
    params: { before }
  });
}

/** 清理已完成消息 */
export function fetchCleanupCompletedMessages(retentionDays: number = 30) {
  return request<number>({
    url: '/api/v2/messages/cleanup/completed',
    method: 'DELETE',
    params: { retentionDays }
  });
}

/** 预热消息缓存 */
export function fetchWarmupMessageCache(customerId: number) {
  return request<void>({
    url: '/api/v2/messages/cache/warmup',
    method: 'POST',
    params: { customerId }
  });
}

/** 刷新统计缓存 */
export function fetchRefreshStatisticsCache(customerId: number) {
  return request<void>({
    url: '/api/v2/messages/cache/refresh-statistics',
    method: 'POST',
    params: { customerId }
  });
}

/** 批量导出消息 */
export function fetchExportMessages(queryDTO: Api.Health.DeviceMessageV2SearchParams) {
  return request<Array<Record<string, any>>>({
    url: '/api/v2/messages/export',
    method: 'POST',
    data: queryDTO
  });
}

// =============== V1兼容性API ===============

/** V1兼容性分页查询 */
export function fetchGetDeviceMessageV1Compatible(params?: Api.Health.DeviceMessageSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.DeviceMessageList>({
    url: '/t_device_message/page',
    method: 'GET',
    params: filteredParams
  });
}

/** V1兼容性获取统计 */
export function fetchGetV1CompatibleStatistics(params?: { deviceSn?: string; userId?: string }) {
  return request<Api.Common.ResponseResult<any>>({
    url: '/t_device_message/statistics',
    method: 'GET',
    params
  });
}

/** V1兼容性确认消息 */
export function fetchAcknowledgeV1Message(messageId: number, deviceSn: string) {
  return request<boolean>({
    url: `/t_device_message/${messageId}/acknowledge`,
    method: 'POST',
    params: { deviceSn }
  });
}

/** V1兼容性获取未读数量 */
export function fetchGetV1UnreadCount(deviceSn: string) {
  return request<number>({
    url: `/t_device_message/unread-count/${deviceSn}`,
    method: 'GET'
  });
}

/** V1兼容性获取设备消息列表 */
export function fetchGetV1DeviceMessages(deviceSn: string, limit: number = 50) {
  return request<Api.Health.DeviceMessage[]>({
    url: `/t_device_message/device/${deviceSn}/messages`,
    method: 'GET',
    params: { limit }
  });
}

/** V1兼容性健康检查 */
export function fetchV1HealthCheck() {
  return request<Api.Common.ResponseResult<any>>({
    url: '/t_device_message/health-check',
    method: 'GET'
  });
}

/** V1兼容性获取版本信息 */
export function fetchGetV1VersionInfo() {
  return request<Api.Common.ResponseResult<any>>({
    url: '/t_device_message/version',
    method: 'GET'
  });
}
