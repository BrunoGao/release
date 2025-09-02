import { request } from '@/service/request';

// =============== Geofence Begin ===============

/** get geofence list */
export function fetchGetGeofenceList(params?: Api.Geofence.GeofenceSearchParams) {
  return request<Api.Geofence.GeofenceList>({
    url: '/t_geofence/page',
    method: 'GET',
    params
  });
}

/** add geofence info */
export function fetchAddGeofence(data: Api.Geofence.GeofenceEdit) {
  return request<boolean>({
    url: '/t_geofence/',
    method: 'POST',
    data
  });
}

/** update geofence info */
export function fetchUpdateGeofenceInfo(data: Api.Geofence.GeofenceEdit) {
  return request<boolean>({
    url: '/t_geofence/',
    method: 'PUT',
    data
  });
}

/** edit delete geofence */
export function fetchDeleteGeofence(data: Api.Common.DeleteParams) {
  return request<boolean>({
    url: '/t_geofence/',
    method: 'DELETE',
    data
  });
}

// =============== Geofence End  ===============
