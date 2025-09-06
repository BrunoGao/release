declare namespace Api {
  namespace Health {
    type DeviceInfo = Common.CommonRecord<{
      orgId: string;
      userId: string;
      systemSoftwareVersion: string;
      wifiAddress: string;
      bluetoothAddress: string;
      ipAddress: string;
      networkAccessMode: number;
      serialNumber: string;
      deviceName: string;
      imei: string;
      createdAt: string;
      batteryLevel: number;
      voltage: number;
      model: string;
      status: string;
      wearableStatus: number;
      chargingStatus: number;
    }>;

    /** DeviceInfo search params */
    type DeviceInfoSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.DeviceInfo, 'imei' | 'model' | 'status' | 'wearableStatus' | 'chargingStatus' | 'orgId' | 'userId'> &
        Api.Common.CommonSearchParams
    >;

    /** DeviceInfo edit model */
    type DeviceInfoEdit = Pick<
      Api.Health.DeviceInfo,
      | 'systemSoftwareVersion'
      | 'wifiAddress'
      | 'bluetoothAddress'
      | 'ipAddress'
      | 'networkAccessMode'
      | 'serialNumber'
      | 'deviceName'
      | 'imei'
      | 'createdAt'
      | 'batteryLevel'
      | 'voltage'
      | 'model'
      | 'status'
      | 'wearableStatus'
      | 'chargingStatus'
      | 'userId'
    >;
    /** DeviceInfo list */
    type DeviceInfoList = Common.PaginatingQueryRecord<DeviceInfo>;

    type DeviceUser = Common.CommonRecord<{
      /** 设备ID */
      deviceId: number;
      /** 用户ID */
      userId: number;
      /** 绑定时间 */
      bindTime: string;
      /** 解绑时间 */
      unbindTime: string;
      /** 绑定状态 (BIND:绑定, UNBIND:解绑) */
      status: any;
      /** 创建用户 */
      createUser: string;
      /** 创建时间 */
      createTime: string;
    }>;

    /** DeviceUser search params */
    type DeviceUserSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.DeviceUser, 'deviceId' | 'userId' | 'status'> & Api.Common.CommonSearchParams
    >;

    /** DeviceUser edit model */
    type DeviceUserEdit = Pick<
      Api.Health.DeviceUser,
      'id' | 'deviceId' | 'userId' | 'bindTime' | 'unbindTime' | 'status' | 'createUser' | 'createTime'
    >;

    /** DeviceUser list */
    type DeviceUserList = Common.PaginatingQueryRecord<DeviceUser>;
  }
}
