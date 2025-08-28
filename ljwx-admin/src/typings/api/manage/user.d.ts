declare namespace Api {
  namespace SystemManage {
    /**
     * user gender
     *
     * - "0": "confidential"
     * - "1": "male"
     * - "2": "female"
     */
    type UserGender = '0' | '1' | '2';

    /**
     * user type
     *
     * - "ADMIN": "administrator"
     * - "EMPLOYEE": "employee"
     */
    type UserType = 'ADMIN' | 'EMPLOYEE';

    /**
     * view mode
     *
     * - "all": "all users"
     * - "employee": "employee only"
     * - "admin": "admin only"
     */
    type ViewMode = 'all' | 'employee' | 'admin';

    /** user */
    type User = Common.CommonRecord<{
      /** user name */
      userName: string;
      /** user gender */
      gender: UserGender | null;
      /** user nickname */
      nickName: string;
      /** user real name */
      realName: string;
      /** user phone */
      phone: string;
      /** user email */
      email: string;
      /** user deviceSn */
      deviceSn: string;
      /** user card number */
      userCardNumber: string;
      /** user status */
      status: Common.EnableStatus;
      /** user position */
      position: string;
      /** user working years */
      workingYears: number;
      /** the org ids */
      orgIds: string;
      /** is admin user */
      isAdmin?: boolean;
      /** user type */
      userType?: UserType;
    }>;

    /** user search params */
    type UserSearchParams = CommonType.RecordNullable<
      Pick<Api.SystemManage.User, 'userName' | 'gender' | 'phone' | 'position' | 'userCardNumber' | 'deviceSn' | 'status' | 'orgIds'> &
        Api.Common.CommonSearchParams & {
          /** view mode for user type filtering */
          viewMode?: ViewMode;
        }
    >;

    /** user edit model */
    type UserEdit = Pick<
      Api.SystemManage.User,
      | 'id'
      | 'userName'
      | 'gender'
      | 'nickName'
      | 'realName'
      | 'phone'
      | 'email'
      | 'deviceSn'
      | 'status'
      | 'userCardNumber'
      | 'orgIds'
      | 'workingYears'
    >;

    /** user list */
    type UserList = Common.PaginatingQueryRecord<User>;

    /** user responsibilities */
    type UserResponsibilities = {
      userId: string;
      roleIds: string[];
      positionIds: string[];
      orgUnitsIds: string[];
      orgUnitsPrincipalIds: string[];
    };
  }
}
