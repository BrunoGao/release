<script setup lang="ts">
import { ref, watch } from 'vue';
import { createReusableTemplate } from '@vueuse/core';
import { useRouter } from 'vue-router';
import { $t } from '@/locales';
import type { TotalAlertInfo, TotalDeviceInfo, TotalMessageInfo, TotalUserInfo } from '@/typings/api/health/user-health-data';

defineOptions({
  name: 'CardData'
});

interface CardData {
  key: string;
  title: string;
  values: { label: string; value: number }[];
  color: {
    start: string;
    end: string;
  };
  icon: string;
}

const cardData = ref<CardData[]>([]);

const props = defineProps<{
  deviceInfo: TotalDeviceInfo;
  userInfo: TotalUserInfo;
  messageInfo: TotalMessageInfo;
  alertInfo: TotalAlertInfo;
}>();

const router = useRouter();

// 监听所有 props 的变化
watch(
  () => [props.deviceInfo, props.userInfo, props.messageInfo, props.alertInfo],
  () => {
    fetchDeviceInfo();
  },
  { immediate: true } // 立即执行一次
);

// 处理卡片点击
function handleCardClick(key: string) {
  switch (key) {
    case 'device':
      router.push('/device/info');
      break;
    case 'user':
      router.push('/manage/user');
      break;
    case 'message':
      router.push('/device/message');
      break;
    case 'alert':
      router.push('/alert/info');
      break;
    default:
      break;
  }
}

function fetchDeviceInfo() {
  try {
    if (!props.deviceInfo || !props.userInfo || !props.messageInfo || !props.alertInfo) {
      console.error('Missing required props');
      return;
    }

    cardData.value = [
      {
        key: 'device',
        title: `${$t('page.home.device.name')} : ${props.deviceInfo.totalDevices || 0}`,
        values: [
          {
            label: $t('page.home.device.online'),
            value: props.deviceInfo?.deviceStatusCounts?.ACTIVE || 0
          },
          {
            label: $t('page.home.device.update'),
            value: props.deviceInfo?.deviceOsCounts?.['ARC-AL00CN 4.0.0.900(SP41C700E104R412P100)'] || 0
          },
          {
            label: $t('page.home.device.wearing'),
            value: props.deviceInfo?.deviceWearableCounts?.WORN || 0
          },
          {
            label: $t('page.home.device.charging'),
            value: props.deviceInfo?.deviceChargingCounts?.CHARGING || 0
          }
        ],
        color: {
          start: '#865ec0',
          end: '#5144b4'
        },
        icon: 'ant-design:mobile-outlined'
      },
      {
        key: 'user',
        title: `${$t('page.home.user.name')} : ${props.userInfo.totalUsers || 0}`,
        values: [
          { label: $t('page.home.user.enable'), value: props.userInfo?.userStatusCounts?.['1'] || 0 },
          { label: $t('page.home.user.bind'), value: props.userInfo?.deviceBindCounts?.BOUND || 0 }
        ],
        color: {
          start: '#ec4786',
          end: '#b955a4'
        },
        icon: 'ant-design:user-outlined'
      },
      {
        key: 'message',
        title: `${$t('page.home.message.name')} : ${props.messageInfo.totalMessages || 0}`,
        values: [
          { label: $t('page.home.message.announcement'), value: props.messageInfo?.messageTypeCounts?.announcement || 0 },
          { label: $t('page.home.message.job'), value: props.messageInfo?.messageTypeCounts?.job || 0 },
          { label: $t('page.home.message.task'), value: props.messageInfo?.messageTypeCounts?.task || 0 },
          { label: $t('page.home.message.notification'), value: props.messageInfo?.messageTypeCounts?.notification || 0 }
        ],
        color: {
          start: '#56cdf3',
          end: '#719de3'
        },
        icon: 'ant-design:message-outlined'
      },
      {
        key: 'alert',
        title: `${$t('page.home.alert.name')} : ${props.alertInfo.totalAlerts || 0}`,
        values: [
          { label: $t('page.home.alert.critical'), value: props.alertInfo?.severityLevelCounts?.critical || 0 },
          {
            label: $t('page.home.alert.high'),
            value: (props.alertInfo?.severityLevelCounts?.high || 0) + (props.alertInfo?.severityLevelCounts?.medium || 0)
          }
        ],
        color: {
          start: '#fcbc25',
          end: '#f68057'
        },
        icon: 'ant-design:alert-outlined'
      }
    ];
  } catch (error) {
    console.error('Error fetching device info:', error);
  }
}

interface GradientBgProps {
  gradientColor: string;
}

const [DefineGradientBg, GradientBg] = createReusableTemplate<GradientBgProps>();

function getGradientColor(color: CardData['color']) {
  return `linear-gradient(to bottom right, ${color.start}, ${color.end})`;
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <DefineGradientBg v-slot="{ $slots, gradientColor }">
      <div class="hover:card-shadow cursor-pointer rd-8px px-16px pb-4px pt-8px text-white" :style="{ backgroundImage: gradientColor }">
        <component :is="$slots.default" />
      </div>
    </DefineGradientBg>

    <NGrid cols="s:1 m:2 l:4" responsive="screen" :x-gap="16" :y-gap="16">
      <NGi v-for="item in cardData" :key="item.key">
        <GradientBg :gradient-color="getGradientColor(item.color)" class="flex-1 p-4" @click="handleCardClick(item.key)">
          <h3 class="mb-2 text-18px font-bold">{{ item.title }}</h3>
          <div class="flex items-start">
            <SvgIcon :icon="item.icon" class="mr-6 text-36px" />
            <div class="w-full flex flex-col items-end">
              <div v-if="item.key === 'device' || item.key === 'message'" class="grid grid-cols-2 w-full gap-2">
                <div v-for="data in item.values" :key="data.label" class="text-right">{{ data.label }}: {{ data.value }}</div>
              </div>
              <div v-else class="flex flex-col gap-2">
                <div v-for="data in item.values" :key="data.label">{{ data.label }}: {{ data.value }}</div>
              </div>
            </div>
          </div>
        </GradientBg>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped>
.card-wrapper {
  border-radius: 8px;
  overflow: hidden;
}

.text-18px {
  font-size: 18px;
}

.text-36px {
  font-size: 36px;
}

.text-14px {
  font-size: 14px;
}

.font-bold {
  font-weight: bold;
}

.font-semibold {
  font-weight: 600;
}

.mb-2 {
  margin-bottom: 8px;
}

.mb-1 {
  margin-bottom: 4px;
}

.mr-6 {
  margin-right: 24px;
}

.p-4 {
  padding: 16px;
}

.grid {
  display: grid;
}

.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.w-full {
  width: 100%;
}

.text-right {
  text-align: left;
}

.hover\:card-shadow:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  transition: all 0.3s;
}

.cursor-pointer {
  cursor: pointer;
}
</style>
