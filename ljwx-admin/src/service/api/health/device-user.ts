import { request } from '@/service/request';

// =============== DeviceUser Begin ===============

/** get deviceUser list */
export function fetchGetDeviceUserList(params?: Api.Health.DeviceUserSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }
  
  return request<Api.Health.DeviceUserList>({
    url: '/t_device_user/page',
    method: 'GET',
    params: filteredParams
  });
}

export function fetchGetUnbindDeviceUserList(params?: Api.Health.DeviceUserSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }
  
  return request<Api.Health.DeviceUserList>({
    url: '/t_device_user/unbind/list',
    method: 'GET',
    params: filteredParams
  });
}

/** add deviceUser info */
export function fetchAddDeviceUser(data: Api.Health.DeviceUserEdit) {
  return request<boolean>({
    url: '/t_device_user/',
    method: 'POST',
    data
  });
}

/** update deviceUser info */
export function fetchUpdateDeviceUserInfo(data: Api.Health.DeviceUserEdit) {
  return request<boolean>({
    url: '/t_device_user/',
    method: 'PUT',
    data
  });
}

/** edit delete deviceUser */
export function fetchDeleteDeviceUser(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_device_user/',
    method: 'DELETE',
    data
  });
}

// =============== DeviceUser End  ===============
