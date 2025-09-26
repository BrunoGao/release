import { request } from '@/service/request';

// =============== Track Begin ===============

/** query history track */
export function fetchQueryHistoryTrack(data: Api.Track.TrackQueryParams) {
  return request<Api.Track.TrackPointList>({
    url: '/track/history',
    method: 'POST',
    data
  });
}

/** query realtime track */
export function fetchQueryRealtimeTrack(data: Api.Track.TrackQueryParams) {
  return request<Api.Track.TrackPointList>({
    url: '/track/realtime',
    method: 'POST',
    data
  });
}

/** query simplified track */
export function fetchQuerySimplifiedTrack(data: Api.Track.TrackQueryParams) {
  return request<Api.Track.TrackPointList>({
    url: '/track/simplified',
    method: 'POST',
    data
  });
}

/** query track statistics */
export function fetchQueryTrackStats(data: Api.Track.TrackStatsQueryParams) {
  return request<Api.Track.TrackStats>({
    url: '/track/stats',
    method: 'POST',
    data
  });
}

/** batch query tracks */
export function fetchBatchQueryTracks(data: Api.Track.TrackQueryParams[]) {
  return request<Api.Track.BatchTrackResult>({
    url: '/track/batch',
    method: 'POST',
    data
  });
}

/** get user latest location */
export function fetchGetLatestLocation(userId: number, deviceSn?: string) {
  const params: any = {};
  if (deviceSn) {
    params.deviceSn = deviceSn;
  }
  
  return request<Api.Track.TrackPoint | null>({
    url: `/track/user/${userId}/latest`,
    method: 'GET',
    params
  });
}

/** query track playback data */
export function fetchQueryTrackPlayback(data: Api.Track.TrackQueryParams) {
  return request<Api.Track.TrackPointList>({
    url: '/track/playback',
    method: 'POST',
    data
  });
}

// =============== Track End ===============