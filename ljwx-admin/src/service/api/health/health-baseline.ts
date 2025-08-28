import { request } from '@/service/request';

// =============== HealthBaseline Begin ===============

/** get healthBaseline list */
export function fetchGetHealthBaselineList(params?: Api.Health.HealthBaselineSearchParams) {
  return request<Api.Health.HealthBaselineList>({
    url: '/t_health_baseline/page',
    method: 'GET',
    params
  });
}

/** add healthBaseline info */
export function fetchAddHealthBaseline(data: Api.Health.HealthBaselineEdit) {
  return request<boolean>({
    url: '/t_health_baseline/',
    method: 'POST',
    data
  });
}

/** update healthBaseline info */
export function fetchUpdateHealthBaselineInfo(data: Api.Health.HealthBaselineEdit) {
  return request<boolean>({
    url: '/t_health_baseline/',
    method: 'PUT',
    data
  });
}

/** edit delete healthBaseline */
export function fetchDeleteHealthBaseline(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_health_baseline/',
    method: 'DELETE',
    data
  });
}

// =============== HealthBaseline End  ===============
