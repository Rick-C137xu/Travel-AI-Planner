<script setup lang="ts">
import { computed, ref } from 'vue';
import PasteGuidePanel from '@/components/PasteGuidePanel.vue';
import PlaceCard from '@/components/PlaceCard.vue';
import PreferenceSummary from '@/components/PreferenceSummary.vue';
import { generateItinerary, recommendPlaces } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';
import type { PlaceStatus } from '@/types';

const { state } = usePlannerStore();
const loadingPlaces = ref(false);
const loadingItinerary = ref(false);
const selectedPlaces = computed(() => state.places.filter((place) => place.userStatus === 'want'));

async function loadPlaces() {
  loadingPlaces.value = true;
  state.warning = '';
  try {
    const response = await recommendPlaces(state.preference, state.guideText);
    state.places = response.data;
    state.warning = response.warning || '';
  } catch (error) {
    state.warning = error instanceof Error ? error.message : '候选地点生成失败';
  } finally {
    loadingPlaces.value = false;
  }
}

function updateStatus(id: string, status: PlaceStatus) {
  state.places = state.places.map((place) => (place.id === id ? { ...place, userStatus: status } : place));
}

async function buildItinerary() {
  loadingItinerary.value = true;
  state.warning = '';
  try {
    const response = await generateItinerary(state.preference, selectedPlaces.value);
    state.itinerary = response.data;
    state.warning = response.warning || '';
    state.step = 'itinerary';
  } catch (error) {
    state.warning = error instanceof Error ? error.message : '行程生成失败';
  } finally {
    loadingItinerary.value = false;
  }
}

if (!state.places.length) {
  void loadPlaces();
}
</script>

<template>
  <section class="two-column wide">
    <div class="places-main">
      <div class="section-head">
        <div>
          <p class="eyebrow">候选地点推荐</p>
          <h2>先挑地点，再排行程</h2>
        </div>
        <div class="head-actions">
          <button class="ghost-btn" :disabled="loadingPlaces" @click="loadPlaces">
            {{ loadingPlaces ? '生成中...' : '重新推荐地点' }}
          </button>
          <button class="primary-btn" :disabled="loadingItinerary || selectedPlaces.length === 0" @click="buildItinerary">
            {{ loadingItinerary ? '生成中...' : `生成行程（${selectedPlaces.length}）` }}
          </button>
        </div>
      </div>
      <p v-if="state.warning" class="warning-banner">{{ state.warning }}</p>
      <PasteGuidePanel />
      <div v-if="loadingPlaces" class="empty-state">正在生成候选地点...</div>
      <div v-else class="place-grid">
        <PlaceCard v-for="place in state.places" :key="place.id" :place="place" @status="updateStatus" />
      </div>
    </div>
    <PreferenceSummary :preference="state.preference" />
  </section>
</template>
