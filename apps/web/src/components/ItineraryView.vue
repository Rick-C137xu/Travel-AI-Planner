<script setup lang="ts">
import { computed, ref } from 'vue';
import { generateItinerary, isFrontendMockMode } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';

const { state, updateRuntimeStatus } = usePlannerStore();
const loading = ref(false);
const selectedPlaces = computed(() => state.places.filter((place) => place.userStatus === 'want'));
const itinerarySource = computed(() => {
  if (isFrontendMockMode) return '前端 Mock 行程模板';
  if (!state.backendConnected) {
    return state.dataSourceLabel === '前端 Mock' ? '后端请求失败 → 前端 Mock' : 'V4 后端';
  }
  if (state.aiEnabled && state.amapEnabled) return 'V4 真实 AI + 高德（按经纬度排序后由 AI 生成行程文案）';
  if (state.amapEnabled) return 'V4 高德排序 + 后端 Mock 行程模板';
  if (state.aiEnabled) return 'V4 AI 行程文案（无地图校验）';
  return 'V3 后端 Mock 行程';
});

function removeItem(day: number, itemId: string) {
  state.itinerary = state.itinerary.map((plan) =>
    plan.day === day ? { ...plan, items: plan.items.filter((item) => item.id !== itemId) } : plan
  );
}

async function regenerate() {
  loading.value = true;
  state.warning = '';
  try {
    const response = await generateItinerary(state.preference, selectedPlaces.value);
    updateRuntimeStatus(response);
    state.itinerary = response.data;
    state.warning = response.warning || '';
  } catch (error) {
    state.warning = error instanceof Error ? error.message : '重新生成行程失败';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="itinerary-panel">
    <div class="section-head">
      <div>
        <p class="eyebrow">每日行程</p>
        <h2>{{ state.preference.destination || '目的地' }} {{ state.preference.days }} 日计划</h2>
      </div>
      <div class="head-actions">
        <button class="ghost-btn" @click="state.step = 'places'">返回选地点</button>
        <button class="primary-btn" :disabled="loading" @click="regenerate">
          {{ loading ? '生成中...' : '重新生成行程' }}
        </button>
      </div>
    </div>
    <p class="source-note">行程来源：{{ itinerarySource }}</p>
    <p v-if="state.warning" class="warning-banner">{{ state.warning }}</p>
    <div v-if="!state.itinerary.length" class="empty-state">还没有行程，请先选择想去的地点。</div>
    <article v-for="day in state.itinerary" :key="day.day" class="day-card">
      <h3>Day {{ day.day }} · {{ day.title }}</h3>
      <p class="date-label">{{ day.date || '日期待定' }}</p>
      <div class="timeline">
        <div v-for="item in day.items" :key="item.id" class="timeline-item">
          <span class="time-label">{{ item.timeLabel }}</span>
          <div>
            <h4>{{ item.placeName }}</h4>
            <p>{{ item.activity }}</p>
            <small>{{ item.estimatedDuration }} · {{ item.transportSuggestion }} · {{ item.note }}</small>
          </div>
          <button class="icon-btn" title="删除该地点" @click="removeItem(day.day, item.id)">×</button>
        </div>
      </div>
    </article>
  </section>
</template>
