<script setup lang="ts">
import { computed, ref } from 'vue';
import { isFrontendMockMode } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';
import type { Place, PlaceStatus } from '@/types';

const props = defineProps<{ place: Place }>();
const emit = defineEmits<{ status: [id: string, status: PlaceStatus] }>();
const { state } = usePlannerStore();

const expanded = ref(false);
const shortReason = computed(() => {
  const reason = props.place.reason || '';
  return reason.length > 54 ? `${reason.slice(0, 54)}...` : reason;
});
const sourceLabel = computed(() => {
  const raw = props.place.source;
  if (raw === 'Mock数据') {
    if (isFrontendMockMode || (state.placeSourceLabel || state.dataSourceLabel) === '前端 Mock') return '前端 Mock';
    if (state.backendConnected && state.aiEnabled === false && state.amapEnabled === false) return '后端 Mock';
  }
  return raw;
});
</script>

<template>
  <article :class="['place-card', place.userStatus]">
    <div class="place-card-head compact-card-head">
      <div class="place-title-block">
        <h3>{{ place.name }}</h3>
        <div class="tag-row">
          <span class="type-tag">{{ place.type }}</span>
          <span class="source-tag">{{ sourceLabel }}</span>
          <span class="mini-tag">{{ place.estimatedTime }}</span>
          <span class="mini-tag">{{ place.suitableFor }}</span>
        </div>
      </div>
    </div>

    <p class="reason">{{ shortReason }}</p>

    <div v-if="expanded" class="place-detail">
      <p v-if="place.address">地址：{{ place.address }}</p>
      <p>避坑：{{ place.warning || '暂无特别提醒' }}</p>
    </div>

    <div class="card-actions">
      <button :class="{ active: place.userStatus === 'want' }" @click="emit('status', place.id, 'want')">想去</button>
      <button :class="{ active: place.userStatus === 'backup' }" @click="emit('status', place.id, 'backup')">备选</button>
      <button :class="{ active: place.userStatus === 'reject' }" @click="emit('status', place.id, 'reject')">不想去</button>
      <button class="detail-toggle" @click="expanded = !expanded">{{ expanded ? '收起' : '详情' }}</button>
    </div>
  </article>
</template>
