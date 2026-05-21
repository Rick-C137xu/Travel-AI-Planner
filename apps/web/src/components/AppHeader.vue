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
  quickStart: '快速开始',
  places: '候选地点',
  itinerary: '每日行程'
};

const versionLabel = computed(() => {
  if (isFrontendMockMode) return 'Travel AI Planner · V4.4.1 Frontend Mock';
  const activeLabel =
    state.step === 'itinerary'
      ? state.itinerarySourceLabel || state.dataSourceLabel
      : state.placeSourceLabel || state.dataSourceLabel;
  if (!state.backendConnected) {
    if (activeLabel === '前端 Mock') return 'Travel AI Planner · Backend Failed → Frontend Mock';
    return 'Travel AI Planner · V4.4.1';
  }
  // V4.3：行程页根据是否拿到真实天气追加 + Weather；候选页保持原标签。
  const onItinerary = state.step === 'itinerary';
  const hasWeather = onItinerary && !!state.weather && state.weather.status === 'ok';
  const weatherSuffix = hasWeather ? ' + Weather' : '';
  const label = activeLabel;
  if (label === '高德地图 + 后端模板') return `Travel AI Planner · V4.4.1 AI Fallback${weatherSuffix}`;
  if (label === '高德地图 + 规则文案') return `Travel AI Planner · V4.4.1 Amap + Rule Copy${weatherSuffix}`;
  if (label === '高德地图 + AI') return `Travel AI Planner · V4.4.1 AI + Amap${weatherSuffix}`;
  if (label === '高德地图') return `Travel AI Planner · V4.4.1 Amap${weatherSuffix}`;
  if (label === 'AI 生成') return `Travel AI Planner · V4.4.1 AI${weatherSuffix}`;
  // dataSourceLabel 尚未拿到时，按后端能力推断
  if (state.aiEnabled && state.amapEnabled) return `Travel AI Planner · V4.4.1 AI + Amap${weatherSuffix}`;
  if (state.amapEnabled) return `Travel AI Planner · V4.4.1 Amap${weatherSuffix}`;
  if (state.aiEnabled) return `Travel AI Planner · V4.4.1 AI${weatherSuffix}`;
  return 'Travel AI Planner · V4.4.1 Backend Mock';
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
