<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { NAlert, NButton, NCard, NCollapse, NCollapseItem, NGi, NGrid, NIcon, NList, NListItem, NSpace, NTag } from 'naive-ui';
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

// 使用手册展开状态
const manualExpanded = ref(['manual']);
</script>

<template>
  <NSpace vertical :size="16">
    <HeaderBanner />

    <!-- 用户使用手册 -->
    <NCard :bordered="false" size="small" class="user-manual">
      <NCollapse v-model:expanded-names="manualExpanded">
        <NCollapseItem name="manual" title="📖 健康监测平台使用手册">
          <template #header-extra>
            <NSpace>
              <NTag type="primary" size="small">快速入门</NTag>
              <span class="text-xs text-gray-500">了解平台核心功能</span>
            </NSpace>
          </template>

          <div class="manual-content">
            <NAlert type="success" :show-icon="false" class="mb-4">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon size="16">
                    <i class="i-material-symbols:dashboard"></i>
                  </NIcon>
                  <span class="font-semibold">数据面板概览</span>
                </div>
              </template>
              首页展示了您的健康监测系统的核心数据统计和实时分析，帮助您快速了解整体运营状况
            </NAlert>

            <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <!-- 设备消息分析 -->
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="18" color="#3b82f6">
                      <i class="i-material-symbols:message"></i>
                    </NIcon>
                    <span class="text-blue-700 font-medium">设备消息分析</span>
                  </div>
                </template>
                <NList size="small">
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">📊</span>
                      <div>
                        <div class="item-title">消息统计卡片</div>
                        <div class="item-desc">显示总消息数、待处理、已处理、响应率等关键指标</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">📈</span>
                      <div>
                        <div class="item-title">消息趋势图表</div>
                        <div class="item-desc">展示消息发送量的时间趋势，帮助分析通信模式</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">📝</span>
                      <div>
                        <div class="item-title">最新消息列表</div>
                        <div class="item-desc">显示最近的设备消息，包括发送状态和响应情况</div>
                      </div>
                    </div>
                  </NListItem>
                </NList>
              </NCard>

              <!-- 告警分析 -->
              <NCard size="small" class="manual-section">
                <template #header>
                  <div class="flex items-center gap-2">
                    <NIcon size="18" color="#ef4444">
                      <i class="i-material-symbols:warning"></i>
                    </NIcon>
                    <span class="text-red-700 font-medium">告警分析</span>
                  </div>
                </template>
                <NList size="small">
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">🚨</span>
                      <div>
                        <div class="item-title">告警统计卡片</div>
                        <div class="item-desc">显示告警总数、紧急告警、处理率等安全指标</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">📉</span>
                      <div>
                        <div class="item-title">告警趋势分析</div>
                        <div class="item-desc">展示告警频率变化，识别健康风险趋势</div>
                      </div>
                    </div>
                  </NListItem>
                  <NListItem>
                    <div class="manual-item">
                      <span class="item-icon">⚡</span>
                      <div>
                        <div class="item-title">紧急告警列表</div>
                        <div class="item-desc">显示最新的紧急告警，需要立即关注和处理</div>
                      </div>
                    </div>
                  </NListItem>
                </NList>
              </NCard>
            </div>

            <!-- 功能操作指南 -->
            <NCard size="small" class="manual-section mt-4">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon size="18" color="#10b981">
                    <i class="i-material-symbols:touch-app"></i>
                  </NIcon>
                  <span class="text-green-700 font-medium">交互操作指南</span>
                </div>
              </template>

              <div class="grid grid-cols-1 mt-3 gap-4 md:grid-cols-3">
                <div class="operation-guide">
                  <div class="guide-header">
                    <NIcon size="16" color="#3b82f6">
                      <i class="i-material-symbols:analytics"></i>
                    </NIcon>
                    <span class="guide-title">数据查看</span>
                  </div>
                  <div class="guide-content">
                    <div class="guide-step">• 点击统计卡片查看详细数据</div>
                    <div class="guide-step">• 鼠标悬停图表查看具体数值</div>
                    <div class="guide-step">• 使用时间筛选器调整数据范围</div>
                  </div>
                </div>

                <div class="operation-guide">
                  <div class="guide-header">
                    <NIcon size="16" color="#f59e0b">
                      <i class="i-material-symbols:manage-search"></i>
                    </NIcon>
                    <span class="guide-title">消息管理</span>
                  </div>
                  <div class="guide-content">
                    <div class="guide-step">• 点击消息列表项查看详情</div>
                    <div class="guide-step">• 查看消息发送状态和响应时间</div>
                    <div class="guide-step">• 跳转到消息管理页面进行处理</div>
                  </div>
                </div>

                <div class="operation-guide">
                  <div class="guide-header">
                    <NIcon size="16" color="#ef4444">
                      <i class="i-material-symbols:emergency"></i>
                    </NIcon>
                    <span class="guide-title">告警处理</span>
                  </div>
                  <div class="guide-content">
                    <div class="guide-step">• 优先处理红色紧急告警</div>
                    <div class="guide-step">• 点击告警项查看健康数据详情</div>
                    <div class="guide-step">• 使用一键处理功能快速响应</div>
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 数据说明 -->
            <NCard size="small" class="manual-section mt-4">
              <template #header>
                <div class="flex items-center gap-2">
                  <NIcon size="18" color="#8b5cf6">
                    <i class="i-material-symbols:help"></i>
                  </NIcon>
                  <span class="text-purple-700 font-medium">数据指标说明</span>
                </div>
              </template>

              <div class="grid grid-cols-1 mt-3 gap-3 lg:grid-cols-4 sm:grid-cols-2">
                <div class="metric-explain">
                  <div class="metric-title">📱 设备状态</div>
                  <div class="metric-content">
                    <span class="metric-item">在线设备数量</span>
                    <span class="metric-item">离线设备数量</span>
                    <span class="metric-item">设备连接率</span>
                  </div>
                </div>

                <div class="metric-explain">
                  <div class="metric-title">👥 用户数据</div>
                  <div class="metric-content">
                    <span class="metric-item">活跃用户数</span>
                    <span class="metric-item">新增用户数</span>
                    <span class="metric-item">用户参与度</span>
                  </div>
                </div>

                <div class="metric-explain">
                  <div class="metric-title">💬 消息分析</div>
                  <div class="metric-content">
                    <span class="metric-item">消息发送量</span>
                    <span class="metric-item">响应成功率</span>
                    <span class="metric-item">平均响应时间</span>
                  </div>
                </div>

                <div class="metric-explain">
                  <div class="metric-title">🚨 告警监控</div>
                  <div class="metric-content">
                    <span class="metric-item">告警总数统计</span>
                    <span class="metric-item">紧急告警数量</span>
                    <span class="metric-item">告警处理效率</span>
                  </div>
                </div>
              </div>
            </NCard>
          </div>
        </NCollapseItem>
      </NCollapse>
    </NCard>

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

<style scoped>
/* 用户使用手册样式 */
.user-manual {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.manual-content {
  padding: 12px;
}

.manual-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.manual-section:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
  transform: translateY(-1px);
}

.manual-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 6px 0;
}

.item-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  border-radius: 6px;
  border: 1px solid #d1d5db;
}

.item-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
  margin-bottom: 3px;
}

.item-desc {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

/* 操作指南样式 */
.operation-guide {
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #0ea5e9;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.operation-guide:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(14, 165, 233, 0.15);
  border-color: #0284c7;
}

.guide-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e0f2fe;
}

.guide-title {
  font-weight: 600;
  color: #0c4a6e;
  font-size: 14px;
}

.guide-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.guide-step {
  font-size: 12px;
  color: #0369a1;
  line-height: 1.4;
  padding: 2px 0;
}

/* 指标说明样式 */
.metric-explain {
  padding: 14px;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  border: 1px solid #a855f7;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.metric-explain:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(168, 85, 247, 0.15);
  border-color: #9333ea;
}

.metric-title {
  font-weight: 600;
  color: #581c87;
  font-size: 13px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 6px;
  border-bottom: 2px solid #f3e8ff;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-item {
  font-size: 11px;
  color: #7c3aed;
  background: rgba(255, 255, 255, 0.7);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #c4b5fd;
  font-weight: 500;
}

/* 折叠面板样式优化 */
:deep(.n-collapse .n-collapse-item .n-collapse-item__header) {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 8px;
  padding: 16px 20px;
  font-weight: 600;
  color: #1e293b;
  border: 1px solid #cbd5e1;
}

:deep(.n-collapse .n-collapse-item .n-collapse-item__header:hover) {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  border-color: #94a3b8;
}

:deep(.n-collapse .n-collapse-item .n-collapse-item__content-wrapper) {
  border-top: 1px solid #e2e8f0;
  margin-top: 8px;
  border-radius: 0 0 8px 8px;
}

/* 响应式优化 */
@media (max-width: 1024px) {
  .grid.grid-cols-1.lg\\:grid-cols-2 {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .manual-content {
    padding: 8px;
  }

  .operation-guide,
  .metric-explain {
    padding: 12px;
  }

  .guide-step,
  .metric-item {
    font-size: 11px;
  }
}

/* 标签样式增强 */
:deep(.n-tag) {
  font-weight: 500;
  border-radius: 6px;
}
</style>
