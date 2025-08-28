/**
 * Namespace Api.Health.AlertConfig
 *
 * Alert configuration related types
 */
declare namespace Api.Health {
  // =============== Alert Config Wechat ===============

  /** wechat alert config */
  interface AlertConfigWechat extends Common.CommonRecord {
    /** customer id */
    customerId: number;
    /** wechat type: enterprise/official */
    type: 'enterprise' | 'official';
    /** enterprise wechat corp id */
    corpId?: string;
    /** enterprise wechat agent id */
    agentId?: string;
    /** enterprise wechat secret */
    secret?: string;
    /** official account app id */
    appid?: string;
    /** official account app secret */
    appsecret?: string;
    /** template id */
    templateId?: string;
    /** enabled status */
    enabled: boolean;
  }

  /** wechat alert config search params */
  interface AlertConfigWechatSearchParams extends Common.CommonSearchParams {
    customerId?: number;
    type?: string;
    corpId?: string;
    appid?: string;
    templateId?: string;
    enabled?: boolean;
  }

  /** wechat alert config edit */
  type AlertConfigWechatEdit = Omit<AlertConfigWechat, 'id' | 'createTime' | 'updateTime'>;

  /** wechat alert config list */
  type AlertConfigWechatList = Common.PaginatingQueryRecord<AlertConfigWechat>;

  // =============== Message Config ===============

  /** message config */
  interface MessageConfig extends Common.CommonRecord {
    /** customer id */
    customerId: number;
    /** config name */
    name: string;
    /** message type: sms/email/webhook/internal */
    type: 'sms' | 'email' | 'webhook' | 'internal';
    /** endpoint (phone/email/url) */
    endpoint: string;
    /** access key */
    accessKey?: string;
    /** secret key */
    secretKey?: string;
    /** template id */
    templateId?: string;
    /** enabled status */
    enabled: boolean;
    /** description */
    description?: string;
  }

  /** message config search params */
  interface MessageConfigSearchParams extends Common.CommonSearchParams {
    customerId?: number;
    name?: string;
    type?: string;
    enabled?: boolean;
  }

  /** message config edit */
  type MessageConfigEdit = Omit<MessageConfig, 'id' | 'createTime' | 'updateTime'>;

  /** message config list */
  type MessageConfigList = Common.PaginatingQueryRecord<MessageConfig>;
}
