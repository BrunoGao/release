import { request } from '@/service/request';

// =============== HealthDataConfig Begin ===============

/** get healthDataConfig list */
export function fetchGetHealthDataConfigList(params?: Api.Customer.HealthDataConfigSearchParams) {
  return request<Api.Customer.HealthDataConfigList>({
    url: '/t_health_data_config/page',
    method: 'GET',
    params
  });
}

/** add healthDataConfig info */
export function fetchAddHealthDataConfig(data: Api.Customer.HealthDataConfigEdit) {
  return request<boolean>({
    url: '/t_health_data_config/',
    method: 'POST',
    data
  });
}

/** update healthDataConfig info */
export function fetchUpdateHealthDataConfigInfo(data: Api.Customer.HealthDataConfigEdit) {
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

// =============== HealthDataConfig End  ===============
