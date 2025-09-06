import { ref } from 'vue';

export const userOptions = ref<Array<{ label: string; value: string }>>([]); // 用户选项列表
export const departmentInfo = ref<string>(''); // 部门信息
