declare namespace Api {
  namespace SystemManage {
    type OrgUnits = Common.CommonRecord<{
      /** org id */
      id: UnionKey.StrNum;
      /** parent org id */
      parentId: UnionKey.StrNum;
      /** org name */
      name: string;
      /** org code */
      code: string;
      /** org abbr */
      abbr: string;
      /** org level */
      level: number;
      /** org ancestors */
      ancestors: string;
      /** org sort */
      description: string;
      /** org sort */
      sort: number;
      /** org status */
      status: Common.EnableStatus;
      /** children org */
      children?: OrgUnits[] | null;
    }>;

    /** OrgUnits page list */
    type OrgUnitsPageList = Common.PaginatingQueryRecord<OrgUnits>;

    /** OrgUnits search params */
    type OrgUnitsSearchParams = CommonType.RecordNullable<
      Pick<Api.SystemManage.OrgUnits, 'name' | 'status' | 'id'> &
        Api.Common.CommonSearchParams & {
          /** customer id for tenant filtering */
          customerId?: UnionKey.StrNum;
        }
    >;

    /** OrgUnits edit model */
    type OrgUnitsEdit = Pick<
      Api.SystemManage.OrgUnits,
      'id' | 'parentId' | 'name' | 'code' | 'abbr' | 'level' | 'ancestors' | 'description' | 'status' | 'sort'
    >;

    /** OrgUnits tree */
    type OrgUnitsTree = Pick<Api.SystemManage.OrgUnits, 'id' | 'name' | 'code'> & {
      children?: OrgUnitsTree[];
    };

    /** Department delete precheck result */
    type DepartmentDeletePreCheck = {
      /** Whether it's safe to delete (no users or devices) */
      canSafeDelete: boolean;
      /** Departments to be deleted */
      departmentsToDelete: {
        orgId: UnionKey.StrNum;
        orgName: string;
        level: number;
        userCount: number;
        deviceCount: number;
      }[];
      /** Users to be deleted */
      usersToDelete: {
        userId: UnionKey.StrNum;
        userName: string;
        realName: string;
        orgName: string;
        deviceSn: string;
        hasDevice: boolean;
      }[];
      /** Devices to be released */
      devicesToRelease: {
        deviceSn: string;
        deviceType: string;
        boundUserId?: UnionKey.StrNum;
        boundUserName?: string;
        orgName?: string;
      }[];
      /** Summary information */
      summary: {
        totalDepartments: number;
        totalUsers: number;
        totalDevices: number;
        usersWithDevices: number;
        warningMessage: string;
      };
    };
  }
}
