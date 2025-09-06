declare namespace Api {
  namespace Customer {
    type Interface = Common.CommonRecord<{
      name: string;
      url: string;
      callInterval: number;
      method: any;
      description: string;
      enabled: number;
      customerId: number;
      apiId: string;
      apiAuth: string;
    }>;

    /** Interface search params */
    type InterfaceSearchParams = CommonType.RecordNullable<Pick<Api.Customer.Interface, 'name' | 'customerId'> & Api.Common.CommonSearchParams>;

    /** Interface edit model */
    type InterfaceEdit = Pick<
      Api.Customer.Interface,
      'name' | 'url' | 'callInterval' | 'method' | 'description' | 'enabled' | 'customerId' | 'apiId' | 'apiAuth'
    >;

    /** Interface list */
    type InterfaceList = Common.PaginatingQueryRecord<Interface>;
  }
}
