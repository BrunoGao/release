import { request } from '@/service/request';

// =============== Health Begin ===============

/** get userDevice list */
export function fetchGetUserDeviceList(params?: Api.Health.UserDeviceSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.UserDeviceList>({
    url: '/t_user_device/page',
    method: 'GET',
    params: filteredParams
  });
}

/** add userDevice info */
export function fetchAddUserDevice(data: Api.Health.UserDeviceEdit) {
  return request<boolean>({
    url: '/t_user_device/',
    method: 'POST',
    data
  });
}

/** update userDevice info */
export function fetchUpdateUserDeviceInfo(data: Api.Health.UserDeviceEdit) {
  return request<boolean>({
    url: '/t_user_device/',
    method: 'PUT',
    data
  });
}

/** edit delete userDevice */
export function fetchDeleteUserDevice(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_user_device/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
