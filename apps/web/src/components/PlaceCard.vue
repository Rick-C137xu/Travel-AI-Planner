<script setup lang="ts">
import type { Place, PlaceStatus } from '@/types';

defineProps<{ place: Place }>();
const emit = defineEmits<{ status: [id: string, status: PlaceStatus] }>();
</script>

<template>
  <article :class="['place-card', place.userStatus]">
    <div class="place-card-head">
      <div>
        <span class="type-tag">{{ place.type }}</span>
        <h3>{{ place.name }}</h3>
      </div>
      <span class="source-tag">{{ place.source }}</span>
    </div>
    <p class="reason">{{ place.reason }}</p>
    <div class="meta-list">
      <span>场景：{{ place.suitableFor }}</span>
      <span>停留：{{ place.estimatedTime }}</span>
      <span v-if="place.address">地址：{{ place.address }}</span>
    </div>
    <p class="warning">避坑：{{ place.warning || '暂无特别提醒' }}</p>
    <div class="card-actions">
      <button :class="{ active: place.userStatus === 'want' }" @click="emit('status', place.id, 'want')">想去</button>
      <button :class="{ active: place.userStatus === 'backup' }" @click="emit('status', place.id, 'backup')">备选</button>
      <button :class="{ active: place.userStatus === 'reject' }" @click="emit('status', place.id, 'reject')">不想去</button>
    </div>
  </article>
</template>
