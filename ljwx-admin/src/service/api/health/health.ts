// @ts-nocheck
import { request } from '@/service/request';
import type { TotalInfo } from '@/typings/api/health/total-info';

// =============== Health Begin ===============

/** Get customer total information */
export function fetchGatherTotalInfo(customerId: number) {
  return request<TotalInfo>({
    url: '/health/gather_total_info',
    method: 'GET',
    params: { org_id: customerId }
  });
}

// =============== 分离式健康数据API ===============

/** 获取基础健康数据列表 - 标准分页查询 */
export function fetchGetHealthDataBasicList(params?: Api.Health.BasicHealthDataSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.BasicHealthDataList>({
    url: '/t_user_health_data/page',
    method: 'GET',
    params: filteredParams
  });
}

/** 获取健康数据分析结果 - 慢数据聚合（专业图表分析） */
export function fetchGetHealthAnalytics(params?: Api.Health.HealthAnalyticsSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.HealthAnalyticsResult>({
    url: '/t_user_health_data/analytics/aggregated',
    method: 'GET',
    params: filteredParams
  });
}

/** 获取睡眠专项分析 */
export function fetchGetSleepAnalytics(params?: Api.Health.HealthAnalyticsSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.SleepAnalyticsResult>({
    url: '/t_user_health_data/analytics/sleep',
    method: 'GET',
    params: filteredParams
  });
}

/** 获取运动专项分析 */
export function fetchGetExerciseAnalytics(params?: Api.Health.HealthAnalyticsSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.ExerciseAnalyticsResult>({
    url: '/t_user_health_data/analytics/exercise',
    method: 'GET',
    params: filteredParams
  });
}

// =============== 健康分析API ===============

/** 获取健康指标统计信息 */
export function fetchHealthMetrics(params?: Api.Health.HealthChartSearchParams) {
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }
  if (!filteredParams.orgId) {
    filteredParams.orgId = '';
  }

  return request<any>({
    url: '/health/analytics/metrics',
    method: 'GET',
    params: filteredParams
  });
}

/** 获取健康评分 */
export function fetchHealthScore(params?: Api.Health.HealthChartSearchParams) {
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }
  if (!filteredParams.orgId) {
    filteredParams.orgId = '';
  }

  return request<any>({
    url: '/health/analytics/score',
    method: 'GET',
    params: filteredParams
  });
}

/** 获取健康建议 */
export function fetchHealthRecommendations(params?: Api.Health.HealthChartSearchParams) {
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }
  if (!filteredParams.orgId) {
    filteredParams.orgId = '';
  }

  return request<any>({
    url: '/health/analytics/recommendations',
    method: 'GET',
    params: filteredParams
  });
}

/** 获取健康趋势分析 */
export function fetchHealthTrends(params?: Api.Health.HealthChartSearchParams & { metricType?: string }) {
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }
  if (!filteredParams.orgId) {
    filteredParams.orgId = '';
  }

  return request<any>({
    url: '/health/analytics/trends',
    method: 'GET',
    params: filteredParams
  });
}

/** 获取综合健康分析 */
export function fetchComprehensiveAnalysis(params?: Api.Health.HealthChartSearchParams) {
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }
  if (!filteredParams.orgId) {
    filteredParams.orgId = '';
  }

  return request<any>({
    url: '/health/analytics/comprehensive',
    method: 'GET',
    params: filteredParams
  });
}
