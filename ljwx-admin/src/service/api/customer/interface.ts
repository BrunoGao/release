import { request } from '@/service/request';

// =============== Health Begin ===============

/** get interface list */
export function fetchGetInterfaceList(params?: Api.Customer.InterfaceSearchParams) {
  return request<Api.Customer.InterfaceList>({
    url: '/t_interface/page',
    method: 'GET',
    params
  });
}

/** add interface info */
export function fetchAddInterface(data: Api.Customer.InterfaceEdit) {
  return request<boolean>({
    url: '/t_interface/',
    method: 'POST',
    data
  });
}

/** update interface info */
export function fetchUpdateInterfaceInfo(data: Api.Customer.InterfaceEdit) {
  return request<boolean>({
    url: '/t_interface/',
    method: 'PUT',
    data
  });
}

/** edit delete interface */
export function fetchDeleteInterface(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_interface/',
    method: 'DELETE',
    data
  });
}

// =============== Health End  ===============
