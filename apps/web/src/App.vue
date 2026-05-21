<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue';
import StartPage from '@/components/StartPage.vue';
import GuidedChat from '@/components/GuidedChat.vue';
import QuickStartForm from '@/components/QuickStartForm.vue';
import PlaceRecommendation from '@/components/PlaceRecommendation.vue';
import ItineraryView from '@/components/ItineraryView.vue';
import MapView from '@/components/MapView.vue';
import { getUserPreferences } from '@/services/userPreferences';
import { usePlannerStore } from '@/store/usePlannerStore';

const { state, resetPlan } = usePlannerStore();
const savedProfile = getUserPreferences();
</script>

<template>
  <AppHeader :step="state.step" @reset="resetPlan" />
  <main class="app-shell">
    <StartPage v-if="state.step === 'start'" />
    <GuidedChat v-else-if="state.step === 'chat'" />
    <QuickStartForm v-else-if="state.step === 'quickStart' && savedProfile" :saved-profile="savedProfile" />
    <PlaceRecommendation v-else-if="state.step === 'places'" />
    <section v-else class="result-grid">
      <ItineraryView />
      <MapView />
    </section>
  </main>
</template>
