import { request } from '@/service/request';

// =============== Health Feature Begin ===============

/** 获取基础健康特征列表 */
export function fetchBaseFeatures(customerId: number) {
  return request<Array<{ label: string; value: string }>>({
    url: '/health/feature/base',
    method: 'GET',
    params: { customerId }
  });
}

/** 获取全量健康特征列表 */
export function fetchFullFeatures(customerId: number) {
  return request<Array<{ label: string; value: string }>>({
    url: '/health/feature/full',
    method: 'GET',
    params: { customerId }
  });
}

/** 获取特征映射关系 */
export function fetchFeatureMapping() {
  return request<Record<string, string[]>>({
    url: '/health/feature/mapping',
    method: 'GET'
  });
}

// =============== Health Feature End ===============
