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
  const { customerId, ...otherParams } = params || {};
  
  if (customerId === undefined || customerId === null) {
    console.warn('customerId is required for optimized org API');
    return fetchGetOrgUnitsPageList(params);
  }
  
  // 超级管理员和租户管理员都使用相同的树形API
  if (customerId === 0) {
    // 超级管理员：使用树形API获取所有租户的树形结构
    console.log('🔧 Super admin: using tree API with customerId=0');
    return request<Api.SystemManage.OrgUnitsTree[]>({
      url: `/sys_org_units/tree?id=${customerId}&customerId=0`,
      method: 'GET'
    }).then(response => {
      // 保持树形结构，不展平
      const treeData = response.data || [];
      
      // 为了兼容分页格式，包装成分页响应
      return {
        ...response,
        data: {
          records: treeData,
          page: 1,
          pageSize: treeData.length,
          total: treeData.length,
          pages: 1
        }
      };
    });
  } else {
    // 租户管理员：使用树形API获取完整树形结构
    console.log('🔧 Tenant admin: using tree API for customerId:', customerId);
    return request<Api.SystemManage.OrgUnitsTree[]>({
      url: `/sys_org_units/tree?id=${customerId}&customerId=${customerId}`,
      method: 'GET'
    }).then(response => {
      // 保持树形结构，不展平
      const treeData = response.data || [];
      
      // 为了兼容分页格式，包装成分页响应
      return {
        ...response,
        data: {
          records: treeData,
          page: 1,
          pageSize: treeData.length,
          total: treeData.length,
          pages: 1
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
