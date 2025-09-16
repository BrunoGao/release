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
  return request<Api.Health.BasicHealthDataList>({
    url: '/t_user_health_data/page',
    method: 'GET',
    params
  });
}

/** 获取健康数据分析结果 - 慢数据聚合（专业图表分析） */
export function fetchGetHealthAnalytics(params?: Api.Health.HealthAnalyticsSearchParams) {
  return request<Api.Health.HealthAnalyticsResult>({
    url: '/t_user_health_data/analytics/aggregated',
    method: 'GET',
    params
  });
}

/** 获取睡眠专项分析 */
export function fetchGetSleepAnalytics(params?: Api.Health.HealthAnalyticsSearchParams) {
  return request<Api.Health.SleepAnalyticsResult>({
    url: '/t_user_health_data/analytics/sleep',
    method: 'GET',
    params
  });
}

/** 获取运动专项分析 */
export function fetchGetExerciseAnalytics(params?: Api.Health.HealthAnalyticsSearchParams) {
  return request<Api.Health.ExerciseAnalyticsResult>({
    url: '/t_user_health_data/analytics/exercise',
    method: 'GET',
    params
  });
}
