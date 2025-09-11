import { request } from '@/service/request';

/**
 * 获取告警处理统计数据
 */
export function fetchGetAlertProcessingStats(params?: {
  customerId?: string;
  startTime?: string;
  endTime?: string;
}) {
  return request<Api.Health.AlertProcessingStats>({
    url: '/admin/health/alert-monitor/stats',
    method: 'GET',
    params
  });
}

/**
 * 获取自动处理日志列表
 */
export function fetchGetAutoProcessingLogs(params?: Api.Health.AlertProcessingLogSearchParams) {
  return request<Api.Health.AlertProcessingLogList>({
    url: '/admin/health/alert-monitor/logs',
    method: 'GET',
    params
  });
}

/**
 * 获取告警处理趋势数据
 */
export function fetchGetProcessingTrends(params?: {
  customerId?: string;
  startTime?: string;
  endTime?: string;
  granularity?: 'hour' | 'day' | 'week';
}) {
  return request<Api.Health.AlertProcessingTrend[]>({
    url: '/admin/health/alert-monitor/trends',
    method: 'GET',
    params
  });
}

/**
 * 获取告警处理汇总数据
 */
export function fetchGetAlertProcessingSummary(params?: {
  customerId?: string;
  period?: 'today' | 'week' | 'month';
}) {
  return request<Api.Health.AlertProcessingSummary>({
    url: '/admin/health/alert-monitor/summary',
    method: 'GET',
    params
  });
}

/**
 * 获取告警处理详情
 */
export function fetchGetAlertProcessingDetail(id: string) {
  return request<Api.Health.AlertProcessingDetail>({
    url: `/admin/health/alert-monitor/detail/${id}`,
    method: 'GET'
  });
}

/**
 * 导出告警处理日志
 */
export function fetchExportAlertProcessingLogs(params?: Api.Health.AlertProcessingLogSearchParams) {
  return request<Blob>({
    url: '/admin/health/alert-monitor/export-logs',
    method: 'POST',
    data: params,
    responseType: 'blob'
  });
}

/**
 * 获取告警处理性能分析
 */
export function fetchGetProcessingPerformanceAnalysis(params?: {
  customerId?: string;
  startTime?: string;
  endTime?: string;
  analysisType?: 'efficiency' | 'accuracy' | 'coverage';
}) {
  return request<Api.Health.AlertProcessingPerformance>({
    url: '/admin/health/alert-monitor/performance',
    method: 'GET',
    params
  });
}