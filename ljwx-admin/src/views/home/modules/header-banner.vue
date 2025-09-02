<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import axios from 'axios';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useAuthStore } from '@/store/modules/auth';

defineOptions({
  name: 'HeaderBanner'
});

const appStore = useAppStore();
const authStore = useAuthStore();

const gap = computed(() => (appStore.isMobile ? 0 : 16));

const weatherDesc = ref('');
const AMAP_KEY = 'd45f28e481665db5b1145a5aa989e68a';

const statisticData1 = ref([
  {
    id: 1,
    title: $t('page.home.projectCount'),
    value: 25,
    suffix: $t('page.home.unit.piece')
  },
  {
    id: 2,
    title: $t('page.home.todoCount'),
    value: 4,
    suffix: $t('page.home.unit.piece')
  },
  {
    id: 3,
    title: $t('page.home.messageCount'),
    value: 10,
    suffix: $t('page.home.unit.piece')
  }
]);

onMounted(async () => {
  try {
    // 1. 先通过 IP 定位获取当前位置
    const locationResponse = await axios.get(`https://restapi.amap.com/v3/ip?key=${AMAP_KEY}`);
    if (!locationResponse.data?.rectangle) {
      throw new Error('Failed to get location');
    }

    // 2. 通过经纬度获取行政区划
    // const [longitude, latitude] = locationResponse.data.rectangle.split(';')[0].split(',');
    const [longitude, latitude] = await getBrowserLocation();
    // const longitude = 114.033382;
    // const latitude = 22.537026;

    console.log(longitude, latitude);
    const districtResponse = await axios.get(
      `https://restapi.amap.com/v3/geocode/regeo?key=${AMAP_KEY}&location=${longitude},${latitude}&extensions=base`
    );
    console.log('districtResponse.data', districtResponse.data);

    if (!districtResponse.data?.regeocode?.addressComponent) {
      throw new Error('Failed to get district info');
    }

    // 获取区级地址
    const { city, district } = districtResponse.data.regeocode.addressComponent;
    const location = `${city}${district}`;

    console.log('location', location);

    // 3. 获取天气信息
    const weatherResponse = await axios.get(`https://restapi.amap.com/v3/weather/weatherInfo?city=${city}&key=${AMAP_KEY}`);

    if (weatherResponse.data?.lives?.[0]) {
      const weatherInfo = weatherResponse.data.lives[0];
      weatherDesc.value = `${location} ${$t('page.home.weather')}: ${weatherInfo.weather}, ${$t('page.home.temperature')}: ${weatherInfo.temperature}°C, ${$t('page.home.humidity')}: ${weatherInfo.humidity}%`;
    } else {
      weatherDesc.value = $t('page.home.weatherUnavailable');
    }
  } catch (error) {
    console.error('Weather API error:', error);
    weatherDesc.value = $t('page.home.weatherError');
  }
});

function getBrowserLocation(): Promise<[number, number]> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        resolve([position.coords.longitude, position.coords.latitude]);
      },
      error => {
        console.error('Geolocation error:', error);
        // 如果地理位置获取失败，使用默认深圳坐标
        resolve([114.033382, 22.537026]);
      },
      {
        timeout: 10000, // 10秒超时
        enableHighAccuracy: false // 不需要高精度
      }
    );
  });
}
</script>

<template>
  <NCard :bordered="false" class="card-wrapper">
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:18">
        <div class="flex-y-center">
          <div class="size-72px shrink-0 overflow-hidden rd-1/2">
            <img src="@/assets/imgs/soybean.jpg" class="size-full" />
          </div>
          <div class="pl-12px">
            <h3 class="text-18px font-semibold">
              {{ $t('page.home.greeting', { userName: authStore.userInfo.userName }) }}
            </h3>
            <p class="text-#999 leading-30px">{{ weatherDesc }}</p>
          </div>
        </div>
      </NGi>
      <NGi span="24 s:24 m:6">
        <NSpace :size="24" justify="end">
          <NStatistic v-for="item in statisticData1" :key="item.id" class="whitespace-nowrap" v-bind="item" />
        </NSpace>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped></style>
