<script setup lang="ts">
import type { AppStep } from '@/types';

defineProps<{ step: AppStep }>();
defineEmits<{ reset: [] }>();

const stepText: Record<AppStep, string> = {
  start: '开始',
  chat: '需求收集',
  places: '候选地点',
  itinerary: '每日行程'
};
</script>

<template>
  <header class="app-header">
    <div>
      <p class="eyebrow">Travel AI Planner · V2.1</p>
      <h1>AI 出行旅游计划助手</h1>
    </div>
    <div class="header-actions">
      <span class="status-pill">{{ stepText[step] }}</span>
      <button class="ghost-btn" @click="$emit('reset')">清空当前计划</button>
    </div>
  </header>
</template>
