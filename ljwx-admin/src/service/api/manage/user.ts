import { request } from '@/service/request';
import { localStg } from '@/utils/storage';
import { getServiceBaseURL } from '@/utils/service';

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

/** batch import users - direct fetch version */
export async function fetchBatchImportUsersDirect(file: File, orgIds: string) {
  console.log('使用直接fetch方法上传文件');
  console.log('API函数收到的文件:', file);
  console.log('文件类型:', typeof file);
  console.log('是否为File实例:', file instanceof File);
  console.log('文件属性:', { name: file.name, size: file.size, type: file.type });

  const formData = new FormData();
  formData.append('file', file);
  formData.append('orgIds', orgIds);

  // 检查FormData内容
  console.log('FormData entries:');
  for (const [key, value] of formData.entries()) {
    console.log(key, value, typeof value);
  }

  // 修复：在生产环境中也应该使用代理前缀（如果配置了VITE_HTTP_PROXY=Y）
  const isHttpProxy = import.meta.env.VITE_HTTP_PROXY === 'Y';
  const { baseURL } = getServiceBaseURL(import.meta.env, isHttpProxy);
  const token = localStg.get('token') || '';
  const authorization = token ? `Bearer ${token}` : '';

  try {
    const response = await fetch(`${baseURL}/sys_user/batch-import`, {
      method: 'POST',
      headers: {
        Authorization: authorization
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return { data: result.data, error: null };
  } catch (error) {
    console.error('直接fetch上传失败:', error);
    return { data: null, error };
  }
}

/** batch import users */
export function fetchBatchImportUsers(file: File, orgIds: string) {
  console.log('API函数收到的文件:', file);
  console.log('文件类型:', typeof file);
  console.log('是否为File实例:', file instanceof File);
  console.log('文件属性:', { name: file.name, size: file.size, type: file.type });

  const formData = new FormData();
  formData.append('file', file);
  formData.append('orgIds', orgIds);

  // 检查FormData内容
  console.log('FormData entries:');
  for (const [key, value] of formData.entries()) {
    console.log(key, value, typeof value);
  }

  return request<{
    success: Array<{ row: number; name: string; userId: string }>;
    failed: Array<{ row: number; reason: string; data: any }>;
    total: number;
  }>({
    url: '/sys_user/batch-import',
    method: 'POST',
    data: formData
  });
}
// =============== User End  ===============
