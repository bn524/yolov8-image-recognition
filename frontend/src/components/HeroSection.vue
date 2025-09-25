<template>
  <section class="hero-section animate-fadeIn">
    <h1 class="hero-title">基于YOLOv8的智能图像识别系统</h1>
    <p class="hero-subtitle">
      使用最新的YOLOv8模型，提供更快速、更准确的目标检测体验。支持批量处理多张图片。
    </p>
  </section>
</template>

<script setup>
// 这个组件主要是展示性内容，不需要响应式数据
</script>

<style scoped>
.hero-section {
  text-align: center;
  margin-bottom: 3rem;
}

.hero-title {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  background: linear-gradient(120deg, var(--primary-color), var(--warning-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
}

.hero-subtitle {
  font-size: 1.2rem;
  color: var(--text-secondary);
  max-width: 700px;
  margin: 0 auto;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fadeIn {
  animation: fadeIn 0.6s ease forwards;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
}
</style>