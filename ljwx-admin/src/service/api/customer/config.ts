import { request } from '@/service/request';

// =============== Health Begin ===============

/** get customerConfig list */
export function fetchGetCustomerConfigList(params?: Api.Customer.CustomerConfigSearchParams) {
  return request<Api.Customer.CustomerConfigList>({
    url: '/t_customer_config/page',
    method: 'GET',
    params
  });
}

/** add customerConfig info */
export function fetchAddCustomerConfig(data: Api.Customer.CustomerConfigEdit) {
  return request<boolean>({
    url: '/t_customer_config/',
    method: 'POST',
    data
  });
}

/** update customerConfig info */
export function fetchUpdateCustomerConfigInfo(data: Api.Customer.CustomerConfigEdit) {
  return request<boolean>({
    url: '/t_customer_config/',
    method: 'PUT',
    data
  });
}

/** edit delete customerConfig */
export function fetchDeleteCustomerConfig(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_customer_config/',
    method: 'DELETE',
    data
  });
}

/** tenant delete precheck - analyze impact */
export function fetchTenantDeletePrecheck(data: Api.Common.DeleteParams) {
  return request<Api.SystemManage.DepartmentDeletePreCheck>({
    url: '/t_customer_config/tenant-delete-precheck',
    method: 'POST',
    data
  });
}

/** tenant cascade delete - including departments, users and devices */
export function fetchTenantCascadeDelete(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_customer_config/tenant-cascade-delete',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
