<template>
  <main class="main-content">
    <div class="container">
      <HeroSection />
      <StatsSection />
      <ImageUploadSection />
      <ResultsSection v-if="analysisResults.length > 0" />
    </div>
  </main>
</template>

<script setup>
import { inject } from 'vue'
import HeroSection from '@/components/HeroSection.vue'
import StatsSection from '@/components/StatsSection.vue'
import ImageUploadSection from '@/components/ImageUploadSection.vue'
import ResultsSection from '@/components/ResultsSection.vue'

const analysisResults = inject('analysisResults')
</script>

<style scoped>
.main-content {
  flex: 1;
  padding: 2rem 0;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}
</style>