declare namespace Api {
  namespace Health {
    type UserDevice = Common.CommonRecord<{
      userid: number;
      deviceSn: string;
      username: string;
      operateTime: string;
      desc: string;
      status: string;
    }>;

    /** UserDevice search params */
    type UserDeviceSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.UserDevice, 'username' | 'deviceSn' | 'status' | 'operateTime'> & Api.Common.CommonSearchParams
    >;

    /** UserDevice edit model */
    type UserDeviceEdit = Pick<Api.Health.UserDevice, 'userid' | 'deviceSn' | 'username' | 'desc' | 'status'>;
    /** UserDevice list */
    type UserDeviceList = Common.PaginatingQueryRecord<UserDevice>;
  }
}
