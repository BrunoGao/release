// @ts-nocheck
import { request } from '@/service/request';

// =============== Health Begin ===============

/** get healthDataConfig list */
export function fetchGetHealthDataConfigList(params?: Api.Health.HealthDataConfigSearchParams) {
  return request<Api.Health.HealthDataConfigList>({
    url: '/t_health_data_config/page',
    method: 'GET',
    params
  });
}

/** add healthDataConfig info */
export function fetchAddHealthDataConfig(data: Api.Health.HealthDataConfigEdit) {
  return request<boolean>({
    url: '/t_health_data_config/',
    method: 'POST',
    data
  });
}

/** update healthDataConfig info */
export function fetchUpdateHealthDataConfigInfo(data: Api.Health.HealthDataConfigEdit) {
  return request<boolean>({
    url: '/t_health_data_config/',
    method: 'PUT',
    data
  });
}

/** edit delete healthDataConfig */
export function fetchDeleteHealthDataConfig(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_health_data_config/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
