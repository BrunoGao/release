import { request } from '@/service/request';

// =============== Health Begin ===============

/** get userHealthData list */
export function fetchGetUserHealthDataList(params?: Api.Health.UserHealthDataSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.UserHealthDataList>({
    url: '/t_user_health_data/page',
    method: 'GET',
    params: filteredParams
  });
}

export function fetchGetUserHealthDataById(id: string) {
  return request<Api.Health.UserHealthDataList>({
    url: `/t_user_health_data/${id}`,
    method: 'GET'
  });
}

/** add userHealthData info */
export function fetchAddUserHealthData(data: Api.Health.UserHealthDataEdit) {
  return request<boolean>({
    url: '/t_user_health_data/',
    method: 'POST',
    data
  });
}

/** update userHealthData info */
export function fetchUpdateUserHealthDataInfo(data: Api.Health.UserHealthDataEdit) {
  return request<boolean>({
    url: '/t_user_health_data/',
    method: 'PUT',
    data
  });
}

/** edit delete userHealthData */
export function fetchDeleteUserHealthData(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_user_health_data/',
    method: 'DELETE',
    data
  });
}

export function fetchUserHealthData(params?: Api.Health.HealthChartSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams.userId === 'all') {
    delete filteredParams.userId;
  }

  // 确保 orgId 有默认值
  if (!filteredParams.orgId) {
    filteredParams.orgId = '';
  }

  return request({
    url: '/t_user_health_data/getUserHealthData',
    params: filteredParams
  });
}

// =============== Health End  ===============
