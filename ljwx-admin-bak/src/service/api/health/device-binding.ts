import { request } from '@/service/request';

// 设备绑定申请相关接口

/** 检查设备绑定状态 */
export function fetchDeviceBindingStatus(params: Api.DeviceBinding.CheckBindingParams) {
  return request<Api.DeviceBinding.CheckBindingResult>({
    url: '/api/device/check_binding',
    method: 'post',
    data: params
  });
}

/** 提交设备绑定申请 */
export function submitDeviceBindingApplication(params: Api.DeviceBinding.SubmitApplicationParams) {
  return request<Api.DeviceBinding.SubmitApplicationResult>({
    url: '/api/device/binding_application',
    method: 'post',
    data: params
  });
}

/** 获取设备绑定申请列表 */
export function fetchDeviceBindingApplications(params?: Api.DeviceBinding.ApplicationSearchParams) {
  return request<Api.DeviceBinding.ApplicationListResult>({
    url: '/api/device/applications',
    method: 'get',
    params
  });
}

/** 批量审批设备绑定申请 */
export function batchApproveBindingApplications(params: Api.DeviceBinding.BatchApproveParams) {
  return request<Api.DeviceBinding.BatchApproveResult>({
    url: '/api/device/batch_approve',
    method: 'post',
    data: params
  });
}

/** 获取用户设备绑定列表 */
export function fetchUserDeviceBindings(userId: string) {
  return request<Api.DeviceBinding.UserBindingListResult>({
    url: '/api/device/user_bindings',
    method: 'get',
    params: { userId }
  });
}
