import { request } from '@/service/request';

// =============== HealthScore Begin ===============

/** get healthScore list */
export function fetchGetHealthScoreList(params?: Api.Health.HealthScoreSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.HealthScoreList>({
    url: '/t_health_score/page',
    method: 'GET',
    params: filteredParams
  });
}

/** add healthScore info */
export function fetchAddHealthScore(data: Api.Health.HealthScoreEdit) {
  return request<boolean>({
    url: '/t_health_score/',
    method: 'POST',
    data
  });
}

/** update healthScore info */
export function fetchUpdateHealthScoreInfo(data: Api.Health.HealthScoreEdit) {
  return request<boolean>({
    url: '/t_health_score/',
    method: 'PUT',
    data
  });
}

/** edit delete healthScore */
export function fetchDeleteHealthScore(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_health_score/',
    method: 'DELETE',
    data
  });
}

// =============== HealthScore End  ===============
