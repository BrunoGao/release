<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';
import { fetchGatherTotalInfo } from '@/service/api';
// import type { TotalAlertInfo, TotalDeviceInfo, TotalMessageInfo, TotalUserInfo } from '@/typings/api/health/user-health-data';
import HeaderBanner from './modules/header-banner.vue';
import AlertTimelineChart from './modules/alert-timeline-chart.vue';
import MessageTimelineChart from './modules/message-timeline-chart.vue';
import CardData from './modules/card-data.vue';
import MessageBanner from './modules/message.vue';
import AlertBanner from './modules/alert.vue';

const appStore = useAppStore();
const authStore = useAuthStore();
const customerId = authStore.userInfo?.customerId;

const gap = computed(() => (appStore.isMobile ? 0 : 16));

const alertInfo = ref<any>({});
const messageInfo = ref<any>({});
const deviceInfo = ref<any>({});
const userInfo = ref<any>({});
const isLoading = ref(true);

async function fetchTotalInfo() {
  try {
    const response = await fetchGatherTotalInfo(customerId);
    alertInfo.value = response.data.alertInfo || {};
    messageInfo.value = response.data.messageInfo || {};
    deviceInfo.value = response.data.deviceInfo || {};
    userInfo.value = response.data.userInfo || {};
    isLoading.value = false;
  } catch (error) {
    console.error('获取设备信息错误:', error);
    isLoading.value = false;
  }
}

onMounted(() => {
  fetchTotalInfo();
});
</script>

<template>
  <NSpace vertical :size="16">
    <HeaderBanner />

    <CardData :device-info="deviceInfo" :user-info="userInfo" :message-info="messageInfo" :alert-info="alertInfo" />

    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:14">
        <MessageTimelineChart :message-info="messageInfo" />
      </NGi>
      <NGi span="24 s:24 m:10">
        <AlertTimelineChart :alert-info="alertInfo" />
      </NGi>
    </NGrid>
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:14">
        <MessageBanner :message-info="messageInfo" :customer-id="String(customerId)" />
      </NGi>
      <NGi span="24 s:24 m:10">
        <AlertBanner :alert-info="alertInfo" :customer-id="String(customerId)" />
      </NGi>
    </NGrid>
  </NSpace>
</template>

<style scoped></style>
