import { request } from '@/service/request';

// =============== Health Begin ===============

/** get deviceMessage list */
export function fetchGetDeviceMessageList(params?: Api.Health.DeviceMessageSearchParams) {
  const urlParams = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      urlParams.append(key, value);
    }
  });

  return request<Api.Health.DeviceMessageList>({
    url: `/t_device_message/page?${urlParams.toString()}`,
    method: 'GET'
  });
}

/** add deviceMessage info */
export function fetchAddDeviceMessage(data: Api.Health.DeviceMessageEdit) {
  return request<boolean>({
    url: '/t_device_message/',
    method: 'POST',
    data
  });
}

/** update deviceMessage info */
export function fetchUpdateDeviceMessageInfo(data: Api.Health.DeviceMessageEdit) {
  return request<boolean>({
    url: '/t_device_message/',
    method: 'PUT',
    data
  });
}

/** edit delete deviceMessage */
export function fetchDeleteDeviceMessage(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_device_message/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
