import { request } from '@/service/request';

// =============== OrgUnits Begin ===============

/** get org page list */
export function fetchGetOrgUnitsPageList(params?: Api.SystemManage.OrgUnitsSearchParams) {
  return request<Api.SystemManage.OrgUnitsPageList>({
    url: '/sys_org_units/page',
    method: 'GET',
    params
  });
}

/** get org page list using optimized API */
export function fetchGetOrgUnitsPageListOptimized(params?: Api.SystemManage.OrgUnitsSearchParams) {
  const { customerId, parentId, ...otherParams } = params || {};
  
  if (!customerId) {
    console.warn('customerId is required for optimized org API');
    return fetchGetOrgUnitsPageList(params);
  }
  
  if (parentId === null || parentId === undefined) {
    return request<Api.SystemManage.OrgUnitsPageList>({
      url: `/system/org-optimized/tenants/${customerId}/top-level`,
      method: 'GET',
      params: otherParams
    }).then(response => {
      return {
        ...response,
        data: {
          records: response.data || [],
          page: 1,
          pageSize: response.data?.length || 0,
          total: response.data?.length || 0
        }
      };
    });
  } else {
    return request<Api.SystemManage.OrgUnitsPageList>({
      url: `/system/org-optimized/orgs/${parentId}/children`,
      method: 'GET',
      params: { customerId, ...otherParams }
    }).then(response => {
      return {
        ...response,
        data: {
          records: response.data || [],
          page: 1,
          pageSize: response.data?.length || 0,
          total: response.data?.length || 0
        }
      };
    });
  }
}

/** add org info */
export function fetchAddOrgUnits(data: Api.SystemManage.OrgUnitsEdit) {
  return request<boolean>({
    url: '/sys_org_units/',
    method: 'POST',
    data
  });
}

/** get org info */
export function fetchGetOrgUnits(id: string) {
  return request<Api.SystemManage.OrgUnits>({
    url: `/sys_org_units/${id}`,
    method: 'GET'
  });
}

/** update org info */
export function fetchUpdateOrgUnits(data: Api.SystemManage.OrgUnitsEdit) {
  return request<boolean>({
    url: '/sys_org_units/',
    method: 'PUT',
    data
  });
}

/** edit delete org */
export function fetchDeleteOrgUnits(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/sys_org_units/',
    method: 'DELETE',
    data
  });
}

/** get org page tree */
export function fetchGetOrgUnitsTree(id: number) {
  return request<Api.SystemManage.OrgUnitsTree[]>({
    url: `/sys_org_units/tree?id=${id}`,
    method: 'GET'
  });
}

/** get org tree using optimized API */
export function fetchGetOrgUnitsTreeOptimized(customerId: number, orgId?: number) {
  if (!customerId) {
    console.warn('customerId is required for optimized org tree API');
    return fetchGetOrgUnitsTree(orgId || 0);
  }
  
  if (!orgId) {
    return request<Api.SystemManage.OrgUnitsTree[]>({
      url: `/system/org-optimized/tenants/${customerId}/top-level`,
      method: 'GET'
    });
  } else {
    return request<Api.SystemManage.OrgUnitsTree[]>({
      url: `/system/org-optimized/orgs/${orgId}/descendants`,
      method: 'GET',
      params: { customerId }
    });
  }
}

/** get org depth using optimized API */
export function fetchGetOrgDepth(orgId: number, customerId: number) {
  return request<number>({
    url: `/system/org-optimized/orgs/${orgId}/depth`,
    method: 'GET',
    params: { customerId }
  });
}

/** check if org is ancestor of another org */
export function fetchCheckOrgAncestor(ancestorId: number, descendantId: number, customerId: number) {
  return request<boolean>({
    url: `/system/org-optimized/orgs/is-ancestor`,
    method: 'GET',
    params: { ancestorId, descendantId, customerId }
  });
}

/** batch find descendants for multiple orgs */
export function fetchBatchOrgDescendants(orgIds: number[], customerId: number) {
  return request<Api.SystemManage.OrgUnits[]>({
    url: `/system/org-optimized/orgs/batch-descendants`,
    method: 'POST',
    data: orgIds,
    params: { customerId }
  });
}

// =============== OrgUnits End  ===============
