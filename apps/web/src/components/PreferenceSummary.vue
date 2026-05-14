<script setup lang="ts">
import type { TravelPreference } from '@/types';

defineProps<{ preference: TravelPreference }>();

const paceMap = { relaxed: '轻松', normal: '正常', intense: '特种兵' };
const budgetMap = { low: '低', medium: '中', high: '高' };
</script>

<template>
  <aside class="summary-panel">
    <h3>旅行需求摘要</h3>
    <dl>
      <template v-if="preference.destination">
        <dt>目的地</dt>
        <dd>{{ preference.destination }}</dd>
      </template>
      <template v-if="preference.startDate">
        <dt>日期</dt>
        <dd>{{ preference.startDate }} 起 · {{ preference.days }} 天</dd>
      </template>
      <template v-if="preference.peopleCount">
        <dt>人数</dt>
        <dd>{{ preference.peopleCount }} 人</dd>
      </template>
      <dt>强度</dt>
      <dd>{{ paceMap[preference.pace] }}</dd>
      <dt>兴趣</dt>
      <dd>{{ preference.interests.length ? preference.interests.join('、') : '未选择' }}</dd>
      <dt>雷区</dt>
      <dd>{{ preference.dislikes.length ? preference.dislikes.join('、') : '无' }}</dd>
      <dt>预算</dt>
      <dd>{{ budgetMap[preference.budgetLevel] }}</dd>
      <dt>住宿</dt>
      <dd>{{ preference.hotelArea || '未填写' }}</dd>
      <dt>交通</dt>
      <dd>{{ preference.transportPreference.length ? preference.transportPreference.join('、') : '未选择' }}</dd>
    </dl>
  </aside>
</template>
