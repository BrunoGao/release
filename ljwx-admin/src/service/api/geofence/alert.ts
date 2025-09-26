import { request } from '@/service/request';

// =============== Geofence Alert Begin ===============

/** get geofence alert list */
export function fetchGetGeofenceAlertList(params?: Api.Geofence.GeofenceAlertSearchParams) {
  return request<Api.Geofence.GeofenceAlertList>({
    url: '/geofence/alert/page',
    method: 'GET',
    params
  });
}

/** get geofence alert detail */
export function fetchGetGeofenceAlertDetail(alertId: string) {
  return request<Api.Geofence.GeofenceAlert>({
    url: `/geofence/alert/${alertId}`,
    method: 'GET'
  });
}

/** process geofence alert */
export function fetchProcessGeofenceAlert(data: Api.Geofence.GeofenceAlertProcess) {
  return request<boolean>({
    url: '/geofence/alert/process',
    method: 'POST',
    data
  });
}

/** batch process geofence alerts */
export function fetchBatchProcessGeofenceAlerts(data: Api.Geofence.GeofenceAlertProcess[]) {
  return request<Record<string, boolean>>({
    url: '/geofence/alert/batch-process',
    method: 'POST',
    data
  });
}

/** get geofence alert stats */
export function fetchGetGeofenceAlertStats(params?: Api.Geofence.GeofenceAlertSearchParams) {
  return request<Api.Geofence.GeofenceAlertStats>({
    url: '/geofence/alert/stats',
    method: 'GET',
    params
  });
}

/** check geofence events */
export function fetchCheckGeofenceEvents(data: Api.Track.TrackPoint) {
  return request<Api.Geofence.GeofenceEvent[]>({
    url: '/geofence/alert/check-events',
    method: 'POST',
    data
  });
}

/** batch check geofence events */
export function fetchBatchCheckGeofenceEvents(data: Api.Track.TrackPoint[]) {
  return request<Record<number, Api.Geofence.GeofenceEvent[]>>({
    url: '/geofence/alert/batch-check-events',
    method: 'POST',
    data
  });
}

/** get recent geofence alerts */
export function fetchGetRecentGeofenceAlerts(limit = 10, userId?: number) {
  const params: any = { limit };
  if (userId) params.userId = userId;
  
  return request<Api.Geofence.GeofenceAlert[]>({
    url: '/geofence/alert/recent',
    method: 'GET',
    params
  });
}

/** initialize geofence geo index */
export function fetchInitializeGeofenceGeoIndex() {
  return request<string>({
    url: '/geofence/alert/initialize-geo-index',
    method: 'POST'
  });
}

// =============== Geofence Alert End ===============