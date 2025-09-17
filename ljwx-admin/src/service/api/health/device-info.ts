import { request } from '@/service/request';

// =============== Health Begin ===============

/** get deviceInfo list */
export function fetchGetDeviceInfoList(params?: Api.Health.DeviceInfoSearchParams) {
  // Filter out userId if it's 'all'
  const filteredParams = { ...params };
  if (filteredParams?.userId === 'all') {
    delete filteredParams.userId;
  }

  return request<Api.Health.DeviceInfoList>({
    url: '/t_device_info/page',
    method: 'GET',
    params: filteredParams
  });
}

export function fetchUnboundDeviceSerialNumbers() {
  return request<Api.Health.DeviceInfoList>({
    url: '/t_device_info/unbound-device-serial-numbers',
    method: 'GET'
  });
}

/** add deviceInfo info */
export function fetchAddDeviceInfo(data: Api.Health.DeviceInfoEdit) {
  return request<boolean>({
    url: '/t_device_info/',
    method: 'POST',
    data
  });
}

/** update deviceInfo info */
export function fetchUpdateDeviceInfoInfo(data: Api.Health.DeviceInfoEdit) {
  return request<boolean>({
    url: '/t_device_info/',
    method: 'PUT',
    data
  });
}

/** edit delete deviceInfo */
export function fetchDeleteDeviceInfo(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_device_info/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
