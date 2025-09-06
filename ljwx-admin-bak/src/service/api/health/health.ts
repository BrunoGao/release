// @ts-nocheck
import { request } from '@/service/request';
import type { TotalInfo } from '@/typings/api/health/total-info';

// =============== Health Begin ===============

/** Get customer total information */
export function fetchGatherTotalInfo(customerId: number) {
  return request<TotalInfo>({
    url: '/health/gather_total_info',
    method: 'GET',
    params: { customer_id: customerId }
  });
}
