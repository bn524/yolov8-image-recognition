<template>
  <header class="header fixed-header">
    <div class="container">
      <div class="header-content">
        <div class="logo">
          <i class="fas fa-robot"></i>
          <span>YOLOv8 识别系统</span>
        </div>
        <nav class="nav-links">
          <a href="#" @click.prevent="scrollToTop"><i class="fas fa-home"></i> 首页</a>
          <a href="https://github.com/ultralytics/yolov8" target="_blank">
            <i class="fas fa-info-circle"></i> 关于
          </a>
          <a href="#" @click.prevent="showContact"><i class="fas fa-envelope"></i> 联系</a>
        </nav>
      </div>
    </div>
  </header>
</template>

<script setup>
import { inject } from 'vue'

const showContactModal = inject('showContactModal')

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const showContact = () => {
  showContactModal.value = true
}
</script>

<style scoped>
.fixed-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: linear-gradient(120deg, var(--primary-color), var(--secondary-color));
  color: white;
  padding: 1rem 0;
  box-shadow: var(--box-shadow);
}

.header::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 60%);
  transform: rotate(30deg);
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  font-size: 1.5rem;
}

.logo i {
  font-size: 1.8rem;
  color: #ffd166;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: rgba(255, 255, 255, 0.85);
  text-decoration: none;
  font-weight: 500;
  transition: var(--transition);
  padding: 0.5rem 1rem;
  border-radius: 6px;
}

.nav-links a:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .nav-links {
    gap: 1rem;
  }
  
  .fixed-header {
    padding: 0.5rem 0;
  }
}
</style>