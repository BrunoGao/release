declare namespace Api {
  namespace Geofence {
    type Geofence = Common.CommonRecord<{
      /** 电子围栏名称 */
      name: string;
      /** 围栏区域 */
      area: any;
      /** 围栏描述 */
      description: string;
      /** 围栏状态 */
      status: any;
      /** 创建用户 */
      createUser: string;
      /** 创建时间 */
      createTime: string;
    }>;

    /** Geofence search params */
    type GeofenceSearchParams = CommonType.RecordNullable<Pick<Api.Geofence.Geofence, 'name' | 'status'> & Api.Common.CommonSearchParams>;

    /** Geofence edit model */
    type GeofenceEdit = Pick<Api.Geofence.Geofence, 'id' | 'name' | 'area' | 'description' | 'status'>;

    /** Geofence list */
    type GeofenceList = Common.PaginatingQueryRecord<Geofence>;
  }
}
