import { request } from '@/service/request';

// =============== User Begin ===============

/** get user list */
export function fetchGetUserList(params?: Api.SystemManage.UserSearchParams) {
  return request<Api.SystemManage.UserList>({
    url: '/sys_user/page',
    method: 'GET',
    params
  });
}

/** get user list by view mode */
export function fetchGetUserListByViewMode(params?: Api.SystemManage.UserSearchParams & { viewMode?: Api.SystemManage.ViewMode }) {
  return request<Api.SystemManage.UserList>({
    url: '/sys_user/page',
    method: 'GET',
    params: {
      ...params,
      viewMode: params?.viewMode || 'all'
    }
  });
}

/** user drawer get user info */
export function fetchGetEditUserInfo(id: string) {
  return request<Api.SystemManage.User>({
    url: `/sys_user/${id}`,
    method: 'GET'
  });
}

/** add user info */
export function fetchAddUser(data: Api.SystemManage.UserEdit) {
  return request<boolean>({
    url: '/sys_user/',
    method: 'POST',
    data
  });
}

/** edit update user info */
export function fetchUpdateUserInfo(data: Api.SystemManage.UserEdit) {
  return request<boolean>({
    url: '/sys_user/',
    method: 'PUT',
    data
  });
}

/** edit delete user */
export function fetchDeleteUser(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/sys_user/',
    method: 'DELETE',
    data
  });
}

/** check user device binding before delete */
export function fetchCheckUserDeviceBinding(data: Api.Common.DeleteParams) {
  return request<Array<{ userId: string; userName: string; deviceSn: string }>>({
    url: '/sys_user/check_device_binding',
    method: 'POST',
    data
  });
}



/** edit delete user */
export function fetchResetUserPassword(userId: string) {
  return request<string>({
    url: `/sys_user/reset_password/${userId}`,
    method: 'PUT'
  });
}

/** get user responsibilities */
export function fetchGetUserResponsibilities(userId: string) {
  return request<Api.SystemManage.UserResponsibilities>({
    url: `/sys_user/responsibilities/${userId}`,
    method: 'GET'
  });
}

/** get user responsibilities */
export function fetchSaveUserResponsibilities(data: Api.SystemManage.UserResponsibilities) {
  return request<boolean>({
    url: `/sys_user/responsibilities`,
    method: 'PUT',
    data
  });
}

export function fetchGetUnbindDevice(customerId: number) {
  return request<boolean>({
    url: `/sys_user/get_unbind_device`,
    method: 'GET',
    params: { customerId }
  });
}

export function fetchGetBindDevice(customerId: number) {
  return request<boolean>({
    url: `/sys_user/get_bind_device`,
    method: 'GET',
    params: { customerId }
  });
}
/** get users by organization id */
export function fetchGetUsersByOrgId(orgId: string) {
  return request<{ [key: string]: string }>({
    url: '/sys_user/get_users_by_org_id',
    method: 'GET',
    params: { orgId }
  });
}
// =============== User End  ===============
