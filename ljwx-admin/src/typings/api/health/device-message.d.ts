declare namespace Api {
  namespace Health {
    type DeviceMessage = Common.CommonRecord<{
      messageId: number;
      orgId: string;
      respondedDetail: {
        totalUsersWithDevices: number;
        nonRespondedUsers: {
          departmentName: string;
          userName: string;
        }[];
      };
      userId: string;
      message: string;
      messageType: string;
      senderType: string;
      receiverType: string;
      messageStatus: string;
      respondedNumber: number;
      sentTime: string;
      receivedTime: string;
      createUser: string;
      createTime: string;
    }>;

    /** DeviceMessage search params */
    type DeviceMessageSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.DeviceMessage, 'orgId' | 'userId' | 'messageType' | 'messageStatus'> & Api.Common.CommonSearchParams
    >;

    /** DeviceMessage edit model */
    type DeviceMessageEdit = Pick<
      Api.Health.DeviceMessage,
      | 'messageId'
      | 'orgId'
      | 'userId'
      | 'message'
      | 'messageType'
      | 'senderType'
      | 'receiverType'
      | 'messageStatus'
      | 'respondedNumber'
      | 'sentTime'
      | 'receivedTime'
      | 'createUser'
      | 'createTime'
    >;
    /** DeviceMessage list */
    type DeviceMessageList = Common.PaginatingQueryRecord<DeviceMessage>;
  }
}
