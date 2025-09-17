import { ref } from 'vue';
import { fetchGetBindDevice, fetchGetUnbindDevice, fetchGetUsersByOrgId } from '@/service/api';

export const deviceOptions = ref<{ label: string; value: string }[]>([]);
export const userOptions = ref<{ label: string; value: string }[]>([]);

function safeArrayUpdate<T>(targetRef: { value: T[] }, newData: T[]) {
  try {
    if (!targetRef || typeof targetRef !== 'object' || !('value' in targetRef)) {
      console.error('Invalid target ref for array update');
      return;
    }

    if (!Array.isArray(targetRef.value)) {
      targetRef.value = [];
    }

    if (!Array.isArray(newData)) {
      console.error('New data is not an array');
      return;
    }

    targetRef.value.splice(0, targetRef.value.length, ...newData);
  } catch (error) {
    console.error('Error in safeArrayUpdate:', error);
    if (targetRef && 'value' in targetRef) {
      targetRef.value = newData || [];
    }
  }
}

export async function handleUnbindDevice(customerId: number) {
  try {
    const { error, data: result } = await fetchGetUnbindDevice(customerId);

    if (!error && Array.isArray(result)) {
      const options = [
        { label: '-', value: '-' },
        ...result.map(device => ({
          label: String(device || ''),
          value: String(device || '')
        }))
      ];

      safeArrayUpdate(deviceOptions, options);
      console.log('deviceOptions:', deviceOptions.value);
    } else {
      console.error('Failed to fetch unbind devices or result is not an array');
      safeArrayUpdate(deviceOptions, []);
    }
  } catch (error) {
    console.error('Error fetching unbind devices:', error);
    safeArrayUpdate(deviceOptions, []);
  }
}

export async function handleBindDevice(customerId: number): Promise<number> {
  try {
    const { error, data: result } = await fetchGetBindDevice(customerId);

    if (!error && Array.isArray(result)) {
      const options = [
        ...result.map(device => ({
          label: String(device || ''),
          value: String(device || '')
        }))
      ];

      safeArrayUpdate(deviceOptions, options);
      console.log('deviceOptions:', deviceOptions.value);
      return result.length;
    }
    console.error('Failed to fetch bind devices or result is not an array');
    safeArrayUpdate(deviceOptions, []);
    return 0;
  } catch (error) {
    console.error('Error fetching bind devices:', error);
    safeArrayUpdate(deviceOptions, []);
    return 0;
  }
}

export async function handleBindUsers(departmentId: number): Promise<{ label: string; value: string }[]> {
  try {
    const bigscreenUrl = import.meta.env.VITE_BIGSCREEN_URL || 'http://localhost:5002';
    const response = await fetch(`${bigscreenUrl}/fetch_departments?id=${departmentId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch. Status: ${response.status}`);
    }

    const result = await response.json();

    if (result && typeof result === 'object' && result !== null) {
      const options = [
        ...Object.entries(result).map(([id, name]) => ({
          label: String(name || ''),
          value: String(id || '')
        }))
      ];

      safeArrayUpdate(userOptions, options);
      console.log('userOptions:', userOptions.value);
      return options;
    }
    console.error('Failed to fetch bind users or result is not an object');
    const emptyResult: { label: string; value: string }[] = [];
    safeArrayUpdate(userOptions, emptyResult);
    return emptyResult;
  } catch (error) {
    console.error('Error fetching bind users:', error);
    const emptyResult: { label: string; value: string }[] = [];
    safeArrayUpdate(userOptions, emptyResult);
    return emptyResult;
  }
}

export async function handleBindUsersByOrgId(orgId: string): Promise<{ label: string; value: string }[]> {
  console.log('handleBindUsersByOrgId.orgId', orgId);
  try {
    const { data: result } = await fetchGetUsersByOrgId(orgId);

    if (result?.userMap && Object.keys(result.userMap).length > 0) {
      const options = [
        { label: '全部用户', value: 'all' },
        ...Object.entries(result.userMap).map(([id, name]) => ({
          label: String(name || ''),
          value: String(id || '')
        }))
      ];
      safeArrayUpdate(userOptions, options);
      console.log('userOptions:', userOptions.value);
      return options;
    }

    const emptyOption = [{ label: '暂无用户', value: 'none', disabled: true }];
    safeArrayUpdate(userOptions, emptyOption);
    return emptyOption;
  } catch (error) {
    console.error('Error fetching bind users:', error);
    const emptyResult: { label: string; value: string }[] = [];
    safeArrayUpdate(userOptions, emptyResult);
    return emptyResult;
  }
}
