// @ts-nocheck
import { ref } from 'vue';
import { fetchUserHealthData } from '@/service/api/health';

export function useHealthData() {
  const healthData = ref({
    bloodOxygen: [],
    heartrate: [],
    pressureHigh: [],
    pressureLow: [],
    step: [],
    temperature: [],
    timestamps: []
  });

  async function fetchHealthData(params) {
    try {
      const response = await fetchUserHealthData(params);
      const responseData = response.response.data.data;

      if (responseData && typeof responseData === 'object') {
        healthData.value = Object.keys(responseData).reduce(
          (acc, dateTimeKey) => {
            const hourData = responseData[dateTimeKey];
            const datePart = dateTimeKey.split('T')[0];

            hourData.forEach(data => {
              // Process data...
              const date = new Date(data.timestamp);
              const formattedTime = date.toLocaleTimeString('zh-CN', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: false
              });
              acc.timestamps.push(`${datePart} ${formattedTime}`);
            });
            return acc;
          },
          {
            bloodOxygen: [],
            heartrate: [],
            pressureHigh: [],
            pressureLow: [],
            step: [],
            temperature: [],
            timestamps: []
          }
        );
      }
    } catch (error) {
      console.error('Failed to fetch health data:', error);
    }
  }

  return {
    healthData,
    fetchHealthData
  };
}
