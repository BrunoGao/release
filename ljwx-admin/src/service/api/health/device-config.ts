import { request } from '@/service/request';

// =============== Heath Begin ===============

/** get deviceConfig list */
export function fetchGetDeviceConfigList(params?: Api.Health.DeviceConfigSearchParams) {
  return request<Api.Health.DeviceConfigList>({
    url: '/t_device_config/page',
    method: 'GET',
    params
  });
}

/** add deviceConfig info */
export function fetchAddDeviceConfig(data: Api.Health.DeviceConfigEdit) {
  return request<boolean>({
    url: '/t_device_config/',
    method: 'POST',
    data
  });
}

/** update deviceConfig info */
export function fetchUpdateDeviceConfigInfo(data: Api.Health.DeviceConfigEdit) {
  return request<boolean>({
    url: '/t_device_config/',
    method: 'PUT',
    data
  });
}

/** edit delete deviceConfig */
export function fetchDeleteDeviceConfig(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_device_config/',
    method: 'DELETE',
    data
  });
}

// =============== Heath End  ===============
