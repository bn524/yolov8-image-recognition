<template>
  <!-- 修复：单根元素 #app -->
  <div id="app">
    <!-- 头部导航（保留原逻辑，移除重复的 HeaderComponent 引用） -->
    <header class="header fixed-header">
      <div class="container">
        <div class="header-content">
          <div class="logo">
            <i class="fas fa-robot"></i>
            <span>YOLOv8 识别系统</span>
          </div>
          <nav class="nav-links">
            <a href="#" @click.prevent="scrollToTop"><i class="fas fa-home"></i> 首页</a>
            <a href="https://docs.ultralytics.com/zh/models/yolov8/" target="_blank"><i class="fas fa-info-circle"></i> 关于</a>
            <a href="#" @click.prevent="showContactModal = true"><i class="fas fa-envelope"></i> 联系</a>
          </nav>
        </div>
      </div>
    </header>

    <div class="header-placeholder"></div>

    <!-- 主内容区（保留原上传/结果逻辑） -->
    <main class="main-content" ref="mainContent">
      <div class="container">
        <section class="hero-section animate-fadeIn">
          <h1 class="hero-title">基于YOLOv8的智能图像识别系统</h1>
          <p class="hero-subtitle">上传您的图片，体验先进的AI视觉识别技术。支持批量处理多张图片。</p>
        </section>

        <div class="stats-container">
          <div class="stat-item">
            <div class="stat-value">99%</div>
            <div class="stat-label">识别准确率</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">0.5s</div>
            <div class="stat-label">平均处理时间</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">80+</div>
            <div class="stat-label">可识别对象</div>
          </div>
        </div>

        <!-- 分析进度提示（补充 missing 的 analyzing/currentAnalyzingIndex 定义） -->
        <div v-if="analyzing" class="progress-indicator">
          <el-progress :percentage="Math.round(((currentAnalyzingIndex + 1) / images.length) * 100)" :stroke-width="8" />
          <p>正在分析第 {{ currentAnalyzingIndex + 1 }} 张，共 {{ images.length }} 张...</p>
        </div>

        <!-- 图片上传组件 -->
        <ImageUpload 
          @analysis-complete="handleAnalysisComplete" 
          @clear-results="clearResults" 
          ref="imageUpload"
        />
        
        <!-- 结果展示区 -->
        <div v-if="analysisResults.length > 0" class="results-container">
          <div class="results-header">
            <h2>分析结果 ({{ analysisResults.length }}张图片)</h2>
            <button class="btn btn-secondary" @click="clearAllResults">
              <i class="fas fa-trash"></i> 清除所有结果
            </button>
          </div>
          
          <div class="results-grid">
            <ResultDisplay 
              v-for="(result, index) in analysisResults" 
              :key="index" 
              :results="result"
              @remove-result="removeResult(index)"
            />
          </div>
        </div>
      </div>
    </main>

    <!-- 页脚（保留原逻辑） -->
    <footer class="footer">
      <div class="container">
        <p>© 2025 YOLOv8图像识别系统 | 基于人工智能的计算机视觉解决方案</p>
      </div>
    </footer>

    <!-- 联系弹窗（修复：仅一处引用） -->
    <ContactModal 
      v-if="showContactModal" 
      @close="showContactModal = false" 
    />
  </div>
</template>

<script>
// 修复：仅导入一次所需组件，路径统一用 @/（指向 src 目录）
import { ref, provide, onMounted } from 'vue'  // Vue 3 选项式 API 中用 onMounted 替代 mounted
import ImageUpload from '@/components/ImageUpload.vue'
import ResultDisplay from '@/components/ResultDisplay.vue'
import ContactModal from '@/components/ContactModal.vue'  // 唯一一次导入

export default {
  name: 'App',
  // 修复：仅注册需要的组件
  components: {
    ImageUpload,
    ResultDisplay,
    ContactModal
  },
  // 修复：统一用选项式 API 的 data 定义响应式数据（无重复）
  data() {
    return {
      showContactModal: false,    // 控制弹窗显示
      analysisResults: [],        // 分析结果列表
      analyzing: false,           // 分析中状态（补充定义，原代码未声明）
      currentAnalyzingIndex: 0,   // 当前分析索引（补充定义）
      images: []                  // 待分析图片列表（补充定义）
    }
  },
  // 修复：用 onMounted 钩子（Vue 3 选项式 API 兼容写法）
  mounted() {
    document.title = "YOLOv8 图像识别系统 - 基于AI的智能视觉识别平台";
  },
  // 修复：统一用 methods 定义方法（无重复）
  methods: {
    // 处理分析完成（接收子组件结果）
    handleAnalysisComplete(results) {
      this.analysisResults.push(results);
    },
    // 清除结果（仅清除数据，不清除图片）
    clearResults() {
      this.analysisResults = [];
    },
    // 清除所有结果和图片（调用子组件 clearAll 方法）
    clearAllResults() {
      this.analysisResults = [];
      this.$refs.imageUpload?.clearAll();  // ?. 避免 ref 未找到时报错
    },
    // 移除单个结果
    removeResult(index) {
      this.analysisResults.splice(index, 1);
    },
    // 回到顶部
    scrollToTop() {
      this.$refs.mainContent?.scrollIntoView({ behavior: 'smooth' });
    }
  },
  // 修复：用选项式 API 的 provide（在 created 钩子中注入，确保数据已初始化）
  created() {
    provide('analysisResults', ref(this.analysisResults));  // 注入响应式结果
    provide('showContactModal', ref(this.showContactModal));// 注入弹窗状态
    provide('handleAnalysisComplete', this.handleAnalysisComplete);
    provide('clearAllResults', this.clearAllResults);
    provide('removeResult', this.removeResult);
  }
}
</script>

<style>
/* 样式部分无错误，保留原代码即可 */
:root {
  --primary-color: #4361ee;
  --secondary-color: #3f37c9;
  --success-color: #4cc9f0;
  --warning-color: #f72585;
  --light-bg: #f8f9fa;
  --dark-bg: #212529;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --border-radius: 12px;
  --box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --header-height: 80px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  color: var(--text-primary);
  min-height: 100vh;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header-placeholder {
  height: var(--header-height);
}

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

.main-content {
  flex: 1;
  padding: 2rem 0;
}

.hero-section {
  text-align: center;
  margin-bottom: 3rem;
}

.hero-title {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  background: linear-gradient(120deg, var(--primary-color), var(--warning-color));
  background-clip: text;
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

.card {
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  overflow: hidden;
  transition: var(--transition);
  margin-bottom: 2rem;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 1.3rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-body {
  padding: 1.5rem;
}

.stats-container {
  display: flex;
  justify-content: space-around;
  margin: 2rem 0;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  flex: 1;
  margin: 0 1rem;
  transition: var(--transition);
}

.stat-item:hover {
  transform: translateY(-5px);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(120deg, var(--primary-color), var(--warning-color));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.footer {
  background: white;
  padding: 1.5rem 0;
  text-align: center;
  color: var(--text-secondary);
  margin-top: auto;
  box-shadow: 0 -5px 15px rgba(0, 0, 0, 0.05);
}

.results-container {
  margin-top: 2rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.results-header h2 {
  color: var(--text-primary);
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  gap: 2rem;
}

.btn {
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: linear-gradient(120deg, var(--primary-color), var(--secondary-color));
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(67, 97, 238, 0.4);
}

.btn-secondary {
  background: white;
  color: var(--text-primary);
  border: 1px solid #d1d8e0;
}

.btn-secondary:hover {
  background: #f8f9fa;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fadeIn {
  animation: fadeIn 0.6s ease forwards;
}

.loading {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .nav-links {
    gap: 1rem;
  }
  
  .stats-container {
    flex-direction: column;
    gap: 1rem;
  }
  
  .stat-item {
    margin: 0;
  }
  
  .hero-title {
    font-size: 2rem;
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .fixed-header {
    padding: 0.5rem 0;
  }
  
  .header-placeholder {
    height: 70px;
  }
}
</style>