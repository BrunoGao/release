declare namespace Api {
  /**
   * namespace Auth
   *
   * backend api module: "auth"
   */
  namespace Auth {
    interface LoginToken {
      token: string;
      refreshToken?: string;  // 可选字段，兼容后端只返回token的情况
    }

    interface UserInfo {
      id: string;
      userName: string;
      nickName: string;
      realName: string;
      roleIds: string[];
      permissions: string[];
      deviceSn: string;
      customerId: number;
    }
  }
}
