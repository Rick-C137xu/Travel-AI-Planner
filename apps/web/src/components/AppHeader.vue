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
  if (isFrontendMockMode) return 'Travel AI Planner · V4.2 Frontend Mock';
  const activeLabel =
    state.step === 'itinerary'
      ? state.itinerarySourceLabel || state.dataSourceLabel
      : state.placeSourceLabel || state.dataSourceLabel;
  if (!state.backendConnected) {
    if (activeLabel === '前端 Mock') return 'Travel AI Planner · Backend Failed → Frontend Mock';
    return 'Travel AI Planner · V4.2';
  }
  // V4.2：按当前页面内容选择候选地点来源或行程来源，避免候选阶段 fallback 污染行程页。
  const label = activeLabel;
  if (label === '高德地图 + 后端模板') return 'Travel AI Planner · V4.2 AI Fallback';
  if (label === '高德地图 + AI') return 'Travel AI Planner · V4.2 AI + Amap';
  if (label === '高德地图') return 'Travel AI Planner · V4.2 Amap';
  if (label === 'AI 生成') return 'Travel AI Planner · V4.2 AI';
  // dataSourceLabel 尚未拿到时，按后端能力推断
  if (state.aiEnabled && state.amapEnabled) return 'Travel AI Planner · V4.2 AI + Amap';
  if (state.amapEnabled) return 'Travel AI Planner · V4.2 Amap';
  if (state.aiEnabled) return 'Travel AI Planner · V4.2 AI';
  return 'Travel AI Planner · V4.2 Backend Mock';
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
