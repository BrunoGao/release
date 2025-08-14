declare namespace Api {
  namespace Health {
    type AlertInfo = Common.CommonRecord<{
      orgId: string;
      userId: string;
      deviceSn: string;
      alertType: string;
      healthId: number;
      alertTimestamp: string;
      alertStatus: string;
      alertDesc: string;
      createUser: string;
      createTime: string;
      severityLevel: string;
      customerId: number;
      ruleId: number;
    }>;

    /** AlertInfo search params */
    type AlertInfoSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.AlertInfo, 'alertType' | 'alertStatus' | 'customerId' | 'orgId' | 'userId'> & Api.Common.CommonSearchParams
    >;

    /** AlertInfo edit model */
    type AlertInfoEdit = Pick<
      Api.Health.AlertInfo,
      'alertType' | 'orgId' | 'userId' | 'alertTimestamp' | 'alertStatus' | 'alertDesc' | 'createUser' | 'createTime' | 'severityLevel'
    >;
    /** AlertInfo list */
    type AlertInfoList = Common.PaginatingQueryRecord<AlertInfo>;

    type AlertConfigWechat = Common.CommonRecord<{
      customerId: number;
      /** WeChat App ID */
      appId: string;
      /** WeChat App Secret */
      appSecret: string;
      /** WeChat Template ID */
      templateId: string;
      /** WeChat User OpenID */
      userOpenid: string;
      /** User who created the record */
      createUser: string;
      /** Creation timestamp */
      createTime: string;
    }>;

    /** Wechaalerconfig search params */
    type AlertConfigWechatSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.AlertConfigWechat, 'appId' | 'appSecret' | 'templateId' | 'userOpenid'> & Api.Common.CommonSearchParams
    >;

    /** Wechaalerconfig edit model */
    type AlertConfigWechatEdit = Pick<
      Api.Health.AlertConfigWechat,
      'id' | 'appId' | 'appSecret' | 'templateId' | 'userOpenid' | 'createUser' | 'createTime'
    >;

    /** Wechaalerconfig list */
    type AlertConfigWechatList = Common.PaginatingQueryRecord<AlertConfigWechat>;
  }
}
