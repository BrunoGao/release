import { shallowRef } from 'vue';
import { fetchGetOrgUnitsTree } from '@/service/api';

/** org units type */
type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;

/** org units tree data */
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);

/** init options */
export async function getOrgUnitsTree(customerId: number) {
  return fetchGetOrgUnitsTree(customerId).then(({ error, data }) => {
    // console.log('getOrgUnitsTree data', data);
    if (!error && data) {
      orgUnitsTree.value = data;
    }
  });
}
