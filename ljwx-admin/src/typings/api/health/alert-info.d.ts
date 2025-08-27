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
      /** WeChat Type: enterprise/official */
      type: string;
      /** Enterprise WeChat Corp ID */
      corpId: string;
      /** Enterprise WeChat Agent ID */
      agentId: string;
      /** Enterprise WeChat Secret */
      secret: string;
      /** Official WeChat App ID */
      appid: string;
      /** Official WeChat App Secret */
      appsecret: string;
      /** WeChat Template ID */
      templateId: string;
      /** Whether enabled */
      enabled: boolean;
      /** User who created the record */
      createUser: string;
      /** Creation timestamp */
      createTime: string;
    }>;

    /** Wechaalerconfig search params */
    type AlertConfigWechatSearchParams = CommonType.RecordNullable<
      Pick<Api.Health.AlertConfigWechat, 'type' | 'corpId' | 'agentId' | 'appid' | 'templateId' | 'enabled'> & Api.Common.CommonSearchParams
    >;

    /** Wechaalerconfig edit model */
    type AlertConfigWechatEdit = Pick<
      Api.Health.AlertConfigWechat,
      'id' | 'customerId' | 'type' | 'corpId' | 'agentId' | 'secret' | 'appid' | 'appsecret' | 'templateId' | 'enabled' | 'createUser' | 'createTime'
    >;

    /** Wechaalerconfig list */
    type AlertConfigWechatList = Common.PaginatingQueryRecord<AlertConfigWechat>;
  }
}
