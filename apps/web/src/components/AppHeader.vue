<script setup lang="ts">
import { computed } from 'vue';
import { isFrontendMockMode } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';
import type { AppStep } from '@/types';

defineProps<{ step: AppStep }>();
defineEmits<{ reset: [] }>();

const { state } = usePlannerStore();

const stepText: Record<AppStep, string> = {
  start: '开始',
  chat: '需求收集',
  places: '候选地点',
  itinerary: '每日行程'
};

const versionLabel = computed(() => {
  if (isFrontendMockMode) return 'Travel AI Planner · V2.1 Frontend Mock';
  if (!state.backendConnected) {
    if (state.dataSourceLabel === '前端 Mock') return 'Travel AI Planner · Backend Failed → Frontend Mock';
    return 'Travel AI Planner · V4.1';
  }
  // V4.1：以本次请求的 dataSourceLabel 为权威，区分 AI 成功/AI 失败降级。
  const label = state.dataSourceLabel;
  if (label === '高德地图 + 后端模板') return 'Travel AI Planner · V4.1 AI Fallback';
  if (label === '高德地图 + AI') return 'Travel AI Planner · V4.1 AI + Amap';
  if (label === '高德地图') return 'Travel AI Planner · V4 Amap';
  if (label === 'AI 生成') return 'Travel AI Planner · V4.1 AI';
  // dataSourceLabel 尚未拿到时，按后端能力推断
  if (state.aiEnabled && state.amapEnabled) return 'Travel AI Planner · V4.1 AI + Amap';
  if (state.amapEnabled) return 'Travel AI Planner · V4 Amap';
  if (state.aiEnabled) return 'Travel AI Planner · V4.1 AI';
  return 'Travel AI Planner · V3 Backend Mock';
});
</script>

<template>
  <header class="app-header">
    <div>
      <p class="eyebrow">{{ versionLabel }}</p>
      <h1>AI 出行旅游计划助手</h1>
    </div>
    <div class="header-actions">
      <span class="status-pill">{{ stepText[step] }}</span>
      <button class="ghost-btn" @click="$emit('reset')">清空当前计划</button>
    </div>
  </header>
</template>
