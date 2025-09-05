<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { fetchUserHealthData } from '@/service/api/health';
import { fetchGetOrgUnitsTree } from '@/service/api';
import { useEcharts } from '@/hooks/common/echarts';
import { handleBindUsersByOrgId } from '@/utils/deviceUtils';
import LineChart from './modules/line-chart.vue';
import TemperatureChart from './modules/temperature.vue';
import BloodOxygenChart from './modules/blood-oxygen.vue';
import StepChart from './modules/step.vue';
import PressureHighChart from './modules/pressure-high.vue';
import PressureLowChart from './modules/pressure-low.vue';
import HealthChartSearch from './modules/health-search.vue';
import SleepChart from './modules/sleep.vue';
import StressChart from './modules/stress.vue';
import CalorieChart from './modules/calorie.vue';
import DistanceChart from './modules/distance.vue';

const authStore = useAuthStore();

const today = new Date();
const startDate = new Date(today.setHours(0, 0, 0, 0)).getTime();
const endDate = new Date(today.setHours(23, 59, 59, 999)).getTime();

const customerId = authStore.userInfo?.customerId;
const searchParams = ref({
  page: 1,
  pageSize: 10,
  orgId: null,
  userId: null,
  startDate,
  endDate,
  timeType: 'day',
  customerId,
  dataType: 'heart_rate'
});

type HealthData = {
  bloodOxygen: number[];
  heartRate: number[];
  pressureHigh: number[];
  pressureLow: number[];
  step: number[];
  temperature: number[];
  timestamps: string[];
  sleep: number[];
  stress: number[];
  calorie: number[];
  distance: number[];
};

const healthData = ref<HealthData>({
  bloodOxygen: [],
  heartRate: [],
  pressureHigh: [],
  pressureLow: [],
  step: [],
  temperature: [],
  timestamps: [],
  sleep: [],
  stress: [],
  calorie: [],
  distance: []
});

function processYearlyMonthlyData(data: any, acc: HealthData, timeKey: string) {
  acc.heartRate.push(Number(data.heartRate) || 0);
  acc.bloodOxygen.push(Number(data.bloodOxygen) || 0);
  acc.pressureHigh.push(Number(data.pressureHigh) || 0);
  acc.pressureLow.push(Number(data.pressureLow) || 0);
  acc.step.push(Number(data.step) || 0);
  acc.temperature.push(Number(data.temperature) || 0);
  acc.sleep.push(Number(data.sleep) || 0);
  acc.stress.push(Number(data.stress) || 0);
  acc.calorie.push(Number(data.calorie) || 0);
  acc.distance.push(Number(data.distance) || 0);
  acc.timestamps.push(String(timeKey || ''));
}

function processDetailedData(data: any, acc: HealthData, timeKey: string) {
  const subKeys = Object.keys(data);
  subKeys.forEach(subTimeKey => {
    const subData = data[subTimeKey];
    if (subData && typeof subData === 'object') {
      acc.heartRate.push(Number(subData.heartRate) || 0);
      acc.bloodOxygen.push(Number(subData.bloodOxygen) || 0);
      acc.pressureHigh.push(Number(subData.pressureHigh) || 0);
      acc.pressureLow.push(Number(subData.pressureLow) || 0);
      acc.step.push(Number(subData.step) || 0);
      acc.temperature.push(Number(subData.temperature) || 0);
      acc.sleep.push(Number(subData.sleep) || 0);
      acc.stress.push(Number(subData.stress) || 0);
      acc.calorie.push(Number(subData.calorie) || 0);
      acc.distance.push(Number(subData.distance) || 0);
      acc.timestamps.push(`${timeKey} ${subTimeKey}`);
    }
  });
}

function initializeHealthDataArrays(acc: HealthData) {
  if (!Array.isArray(acc.heartRate)) acc.heartRate = [];
  if (!Array.isArray(acc.bloodOxygen)) acc.bloodOxygen = [];
  if (!Array.isArray(acc.pressureHigh)) acc.pressureHigh = [];
  if (!Array.isArray(acc.pressureLow)) acc.pressureLow = [];
  if (!Array.isArray(acc.step)) acc.step = [];
  if (!Array.isArray(acc.temperature)) acc.temperature = [];
  if (!Array.isArray(acc.sleep)) acc.sleep = [];
  if (!Array.isArray(acc.stress)) acc.stress = [];
  if (!Array.isArray(acc.calorie)) acc.calorie = [];
  if (!Array.isArray(acc.distance)) acc.distance = [];
  if (!Array.isArray(acc.timestamps)) acc.timestamps = [];
}

async function fetchHealthData() {
  try {
    const response = await fetchUserHealthData({
      customerId: searchParams.value.customerId,
      orgId: searchParams.value.orgId || '',
      userId: searchParams.value.userId,
      startDate: searchParams.value.startDate,
      endDate: searchParams.value.endDate,
      timeType: searchParams.value.timeType,
      dataType: searchParams.value.dataType
    });

    if (!response || !response.response || !response.response.data) {
      throw new Error('Invalid response structure');
    }

    const responseData = response.response.data.data;

    if (responseData && typeof responseData === 'object') {
      const newHealthData = Object.keys(responseData).reduce(
        (acc, timeKey) => {
          const data = responseData[timeKey];

          if (!data || typeof data !== 'object') {
            console.warn(`Invalid data for timeKey ${timeKey}:`, data);
            return acc;
          }

          initializeHealthDataArrays(acc);

          if (searchParams.value.timeType === 'year' || searchParams.value.timeType === 'month') {
            processYearlyMonthlyData(data, acc, timeKey);
          } else if (data && typeof data === 'object') {
            processDetailedData(data, acc, timeKey);
          }

          return acc;
        },
        {
          bloodOxygen: [] as number[],
          heartRate: [] as number[],
          pressureHigh: [] as number[],
          pressureLow: [] as number[],
          step: [] as number[],
          temperature: [] as number[],
          timestamps: [] as string[],
          sleep: [] as number[],
          stress: [] as number[],
          calorie: [] as number[],
          distance: [] as number[]
        }
      );

      Object.assign(healthData.value, newHealthData);
    } else {
      throw new TypeError('Data is not in expected format or success flag is false');
    }
  } catch (error) {
    console.error('Failed to fetch health data:', error);
    healthData.value = {
      bloodOxygen: [],
      heartRate: [],
      pressureHigh: [],
      pressureLow: [],
      step: [],
      temperature: [],
      timestamps: [],
      sleep: [],
      stress: [],
      calorie: [],
      distance: []
    };
  }
}

console.log('Initial dataType:', searchParams.value.dataType);
watch(
  () => searchParams.value.dataType,
  (newValue, oldValue) => {
    console.log(`dataType changed from ${oldValue} to ${newValue}`);
  }
);

console.log('searchParams.value.dataType', searchParams.value.dataType);

type OrgUnitsTree = Api.SystemManage.OrgUnitsTree;

/** org units tree data */
const orgUnitsTree = shallowRef<OrgUnitsTree[]>([]);
const userOptions = ref<{ label: string; value: string }[]>([]);

async function handleInitOptions() {
  fetchGetOrgUnitsTree(customerId).then(({ error, data: treeData }) => {
    if (!error && treeData) {
      orgUnitsTree.value = treeData;
      // 设置默认选中第一个部门
      if (treeData.length > 0) {
        searchParams.value.orgId = treeData[0].id;
        // 初始化时获取第一个部门的员工列表
        handleBindUsersByOrgId(treeData[0].id).then(result => {
          if (Array.isArray(result)) {
            userOptions.value = result;
          }
        });
      }
    }
  });
}

// 监听部门变化，更新员工列表
watch(
  () => searchParams.value.orgId,
  async newValue => {
    if (newValue) {
      const result = await handleBindUsersByOrgId(String(newValue));
      if (Array.isArray(result)) {
        userOptions.value = result;
      }
    }
  }
);

// console.log('healthData2', healthData.value);
onMounted(() => {
  handleInitOptions();
  fetchHealthData();
});
</script>

<template>
  <NSpace vertical :size="16">
    <HealthChartSearch
      v-model:model="searchParams"
      :org-units-tree="orgUnitsTree"
      :user-options="userOptions"
      :customer-id="customerId"
      @search="fetchHealthData"
    />

    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'heart_rate'"
      :bordered="false"
      class=".chart-container"
    >
      <LineChart :data="healthData.heartRate" :timestamps="healthData.timestamps" />
    </NCard>

    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'temperature'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <TemperatureChart :data="healthData.temperature" :timestamps="healthData.timestamps" />
    </NCard>

    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'blood_pressure'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <PressureHighChart :data="healthData.pressureHigh" :timestamps="healthData.timestamps" />
    </NCard>

    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'blood_pressure'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <PressureLowChart :data="healthData.pressureLow" :timestamps="healthData.timestamps" />
    </NCard>

    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'blood_oxygen'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <BloodOxygenChart :data="healthData.bloodOxygen" :timestamps="healthData.timestamps" />
    </NCard>

    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'step'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <StepChart :data="healthData.step" :timestamps="healthData.timestamps" />
    </NCard>

    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'sleep'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <SleepChart :data="healthData.sleep" :timestamps="healthData.timestamps" />
    </NCard>
    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'stress'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <StressChart :data="healthData.stress" :timestamps="healthData.timestamps" />
    </NCard>
    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'calorie'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <CalorieChart :data="healthData.calorie" :timestamps="healthData.timestamps" />
    </NCard>
    <NCard
      v-if="searchParams.dataType === 'all' || searchParams.dataType === null || searchParams.dataType === 'distance'"
      :bordered="false"
      class="chart-container card-wrapper"
    >
      <DistanceChart :data="healthData.distance" :timestamps="healthData.timestamps" />
    </NCard>
  </NSpace>
</template>

<style scoped>
.chart-container {
  height: 600px; /* 调整高度 */
  max-width: 100%; /* 设置最大宽度 */
  margin: 0 auto; /* 居中对齐 */
}
</style>
