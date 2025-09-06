<script setup lang="ts"></script>

<template>
  <div>
    <NCard title="视频播放器插件" :bordered="false" class="h-full card-wrapper">
      <div class="flex-center">
        <div ref="domRef" class="h-auto w-full shadow-md"></div>
      </div>
    </NCard>
  </div>
</template>

<style scoped></style>
