<template>
  <div class="card">
    <div class="card-header">
      <h2 class="card-title"><i class="fas fa-cloud-upload-alt"></i> 图片上传</h2>
      <div class="upload-actions">
        <button class="btn btn-secondary" @click="clearAll" :disabled="!hasImages || analyzing">
          <i class="fas fa-trash"></i> 清除所有图片
        </button>
        <button 
          class="btn btn-primary" 
          @click="analyzeAll" 
          :disabled="!hasImages || analyzing || !backendConnected"
        >
          <span v-if="analyzing" class="loading"></span>
          <i v-else class="fas fa-play"></i>
          {{ analyzing ? `分析中 (${currentAnalyzingIndex + 1}/${images.length})` : '分析全部' }}
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="upload-container">
        <div class="upload-area" @click="triggerFileInput" @drop="handleDrop" @dragover.prevent>
          <i class="upload-icon fas fa-cloud-upload-alt"></i>
          <h3 class="upload-text">拖放图片或点击上传</h3>
          <p class="upload-hint">支持 JPG, PNG 格式，可多选，最大5MB/张</p>
          <input 
            type="file" 
            ref="fileInput" 
            @change="handleFileUpload" 
            accept="image/*" 
            multiple 
            hidden
          >
        </div>

        <!-- 后端连接警告（使用Element Alert，需确保Element UI已引入） -->
        <div v-if="!backendConnected" class="connection-warning">
          <el-alert 
            title="后端连接异常" 
            type="warning" 
            show-icon 
            :closable="false"
          >
            <p>无法连接到检测服务，请确保：</p>
            <p>1. 后端服务已启动（地址：http://localhost:8000）</p>
            <p>2. Vite代理配置正确（/api 指向后端）</p>
          </el-alert>
        </div>

        <!-- 分析进度指示 -->
        <div v-if="analyzing" class="progress-indicator">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: `${((currentAnalyzingIndex + 1) / images.length) * 100}%` }"
            ></div>
          </div>
          <p>正在分析第 {{ currentAnalyzingIndex + 1 }} 张图片，共 {{ images.length }} 张</p>
        </div>

        <div v-if="images.length > 0" class="images-container">
          <h3>已选择 {{ images.length }} 张图片</h3>
          <div class="images-grid">
            <div v-for="(image, index) in images" :key="index" class="image-item">
              <img :src="image.url" :alt="`Preview ${index + 1}`" class="thumbnail">
              <div class="image-overlay">
                <button class="btn-icon" @click="removeImage(index)" :disabled="analyzing">
                  <i class="fas fa-times"></i>
                </button>
                <span class="image-name">{{ image.file.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 若未全局引入Element UI，需单独导入Alert组件（否则el-alert会报错）
import { ElAlert } from 'element-plus';
import 'element-plus/theme-chalk/el-alert.css';

export default {
  name: 'ImageUpload',
  // 注册Element Alert组件
  components: { ElAlert },
  data() {
    return {
      images: [],
      results: [],
      analyzing: false, // 已定义analyzing，解决Vue警告
      currentAnalyzingIndex: 0,
      backendConnected: true, // 后端连接状态
      // 优先使用代理地址（/api/detect），避免直接跨域请求
      apiUrl: import.meta.env.VITE_API_URL || '/api/detect',
      // 后端根路径（用于连接检查，同样走代理）
      backendRootUrl: import.meta.env.VITE_BACKEND_ROOT || '/api/'
    }
  },
  computed: {
    hasImages() {
      return this.images.length > 0
    }
  },
  mounted() {
    // 组件挂载时检查后端连接（使用代理地址）
    this.checkBackendConnection();
  },
  methods: {
    /**
     * 检查后端连接状态（走Vite代理，解决跨域）
     */
    async checkBackendConnection() {
      try {
        const response = await fetch(this.backendRootUrl, {
          method: 'GET',
          timeout: 5000 // 5秒超时，避免长时间等待
        });
        
        if (response.ok) {
          this.backendConnected = true;
          this.showSuccess('后端连接正常');
        } else {
          this.backendConnected = false;
          this.showWarning('后端服务已启动，但响应异常');
        }
      } catch (error) {
        this.backendConnected = false;
        this.showError('后端连接失败，请检查服务是否启动或代理配置是否正确');
        console.error('后端连接检查详情:', error);
      }
    },

    /**
     * 触发隐藏的文件选择框
     */
    triggerFileInput() {
      if (this.$refs.fileInput && !this.analyzing) {
        this.$refs.fileInput.click();
      }
    },
    
    /**
     * 处理文件选择上传
     */
    handleFileUpload(event) {
      const files = Array.from(event.target.files);
      if (files.length === 0 || this.analyzing) return;
      
      this.addImages(files);
      // 清空input值，避免重复选择同一文件
      event.target.value = '';
    },
    
    /**
     * 处理拖放上传
     */
    handleDrop(event) {
      event.preventDefault();
      if (this.analyzing) return;
      
      const files = Array.from(event.dataTransfer.files).filter(file => 
        file.type.startsWith('image/')
      );
      
      if (files.length > 0) {
        this.addImages(files);
      }
    },
    
    /**
     * 新增图片到列表（含格式/大小校验）
     */
    addImages(files) {
      const validImages = files.filter(file => {
        // 格式校验
        if (!file.type.startsWith('image/')) {
          this.showError(`文件 ${file.name} 格式不支持（仅支持图片）`);
          return false;
        }
        // 大小校验（5MB）
        if (file.size > 5 * 1024 * 1024) {
          this.showError(`文件 ${file.name} 太大（最大支持5MB）`);
          return false;
        }
        // 重复校验（按文件名）
        if (this.images.some(img => img.file.name === file.name)) {
          this.showWarning(`文件 ${file.name} 已存在，跳过上传`);
          return false;
        }
        return true;
      });
      
      // 新增有效图片
      validImages.forEach(file => {
        this.images.push({
          file,
          url: URL.createObjectURL(file) // 生成预览地址
        });
      });
    },
    
    /**
     * 移除单张图片
     */
    removeImage(index) {
      if (this.analyzing) return;
      
      // 释放预览地址，避免内存泄漏
      URL.revokeObjectURL(this.images[index].url);
      this.images.splice(index, 1);
    },
    
    /**
     * 清除所有图片
     */
    clearAll() {
      if (this.analyzing) return;
      
      // 批量释放预览地址
      this.images.forEach(image => URL.revokeObjectURL(image.url));
      this.images = [];
      this.results = [];
      // 通知父组件清除结果
      this.$emit('clear-results');
    },
    
    /**
     * 分析所有图片（核心流程）
     */
    async analyzeAll() {
      if (!this.backendConnected) {
        this.showError('后端未连接，无法执行分析');
        return;
      }
      if (this.images.length === 0) {
        this.showWarning('请先选择图片');
        return;
      }
      
      this.analyzing = true;
      let successCount = 0; // 分析成功计数
      let errorCount = 0;   // 分析失败计数
      const total = this.images.length;
      
      try {
        // 逐张分析（避免请求密集）
        for (let i = 0; i < total; i++) {
          this.currentAnalyzingIndex = i;
          const currentImage = this.images[i];
          
          try {
            await this.analyzeImage(currentImage);
            successCount++;
          } catch (error) {
            errorCount++;
            this.showError(`第 ${i + 1} 张图片分析失败：${error.message}`);
            console.error(`第 ${i + 1} 张图片分析详情:`, error);
          }
          
          // 非最后一张图，添加500ms延迟
          if (i < total - 1) {
            await new Promise(resolve => setTimeout(resolve, 500));
          }
        }
        
        // 分析完成，提示结果
        if (errorCount === 0) {
          this.showSuccess(`全部 ${total} 张图片分析成功`);
        } else {
          this.showWarning(`分析完成：成功 ${successCount} 张 / 失败 ${errorCount} 张`);
        }
      } finally {
        // 无论成功失败，重置状态
        this.analyzing = false;
        this.currentAnalyzingIndex = 0;
      }
    },
    
    /**
     * 分析单张图片（调用后端接口）
     */
    async analyzeImage(image) {
      try {
        // 构建FormData（图片上传必须用此格式）
        const formData = new FormData();
        formData.append('file', image.file);
        
        console.log(`发送分析请求：${this.apiUrl}（文件名：${image.file.name}）`);
        const response = await fetch(this.apiUrl, {
          method: 'POST',
          body: formData,
          signal: AbortSignal.timeout(30000), // 30秒超时
          headers: {
            // 无需手动设置Content-Type，浏览器会自动添加正确的boundary
            'X-Requested-With': 'XMLHttpRequest' // 标记为AJAX请求
          }
        });
        
        // 检查响应状态
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('接口不存在，请检查后端路由配置');
          } else if (response.status === 500) {
            throw new Error('后端服务错误，请查看后端日志');
          } else {
            throw new Error(`请求失败（状态码：${response.status}）`);
          }
        }
        
        // 解析响应数据
        const data = await response.json();
        console.log(`第 ${this.currentAnalyzingIndex + 1} 张图片分析结果:`, data);
        
        // 检查后端返回的错误
        if (data.error) {
          throw new Error(data.error);
        }
        
        // 转换结果格式（适配前端展示）
        const detections = this.transformDetectionData(data);
        // 通知父组件分析完成
        this.$emit('analysis-complete', {
          detections,
          imageUrl: image.url,
          fileName: image.file.name,
          timestamp: new Date().toLocaleString()
        });
        
        // 存储结果到本地
        this.results.push({
          imageUrl: image.url,
          fileName: image.file.name,
          detections,
          timestamp: new Date().toLocaleString()
        });
        
      } catch (error) {
        // 特殊错误处理
        if (error.name === 'TimeoutError') {
          this.backendConnected = false;
          throw new Error('请求超时（后端无响应）');
        } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
          this.backendConnected = false;
          throw new Error('网络错误（后端未连接或代理配置错误）');
        } else {
          throw error; // 其他错误直接抛出
        }
      }
    },
    
    /**
     * 转换后端返回的检测数据（适配前端格式）
     */
    transformDetectionData(backendData) {
      const detections = [];
      
      // 检查后端返回数据的完整性
      if (!backendData.boxes || !backendData.classes || !backendData.confidences) {
        throw new Error('后端返回数据不完整（缺少boxes/classes/confidences）');
      }
      
      // 取三个数组的最小长度（避免数组长度不一致导致报错）
      const minLength = Math.min(
        backendData.boxes.length,
        backendData.classes.length,
        backendData.confidences.length
      );
      
      // 转换格式：后端[x1,y1,x2,y2] → 前端[x1,y1,width,height] + 中文类别
      for (let i = 0; i < minLength; i++) {
        const [x1, y1, x2, y2] = backendData.boxes[i];
        detections.push({
          class: this.translateClass(backendData.classes[i]), // 中文类别
          confidence: Number((backendData.confidences[i] * 100).toFixed(2)), // 置信度（%）
          bbox: [x1, y1, x2 - x1, y2 - y1], // 检测框（x,y,宽,高）
          index: i // 序号
        });
      }
      
      return detections;
    },
    
    /**
     * 类别中英文转换（YOLO默认英文 → 中文）
     */
    translateClass(className) {
      const classMap = {
        'person': '人',
        'bicycle': '自行车',
        'car': '汽车',
        'motorcycle': '摩托车',
        'airplane': '飞机',
        'bus': '公交车',
        'train': '火车',
        'truck': '卡车',
        'boat': '船',
        'traffic light': '交通灯',
        'fire hydrant': '消防栓',
        'stop sign': '停止标志',
        'bird': '鸟',
        'cat': '猫',
        'dog': '狗',
        'horse': '马',
        'sheep': '羊',
        'cow': '牛',
        'elephant': '大象',
        'bear': '熊',
        'zebra': '斑马',
        'giraffe': '长颈鹿',
        'backpack': '背包',
        'umbrella': '雨伞',
        'handbag': '手提包',
        'tie': '领带',
        'suitcase': '行李箱',
        'sports ball': '运动球',
        'kite': '风筝',
        'baseball bat': '棒球棒',
        'skateboard': '滑板',
        'surfboard': '冲浪板',
        'tennis racket': '网球拍',
        'bottle': '瓶子',
        'wine glass': '酒杯',
        'cup': '杯子',
        'fork': '叉子',
        'knife': '刀',
        'spoon': '勺子',
        'bowl': '碗',
        'banana': '香蕉',
        'apple': '苹果',
        'sandwich': '三明治',
        'orange': '橙子',
        'broccoli': '西兰花',
        'carrot': '胡萝卜',
        'pizza': '披萨',
        'donut': '甜甜圈',
        'cake': '蛋糕',
        'chair': '椅子',
        'couch': '沙发',
        'potted plant': '盆栽',
        'bed': '床',
        'dining table': '餐桌',
        'toilet': '马桶',
        'tv': '电视',
        'laptop': '笔记本电脑',
        'mouse': '鼠标',
        'remote': '遥控器',
        'keyboard': '键盘',
        'cell phone': '手机',
        'microwave': '微波炉',
        'oven': '烤箱',
        'toaster': '烤面包机',
        'sink': '水槽',
        'refrigerator': '冰箱',
        'book': '书',
        'clock': '时钟',
        'vase': '花瓶',
        'scissors': '剪刀',
        'teddy bear': '泰迪熊',
        'hair drier': '吹风机',
        'toothbrush': '牙刷'
      };
      
      // 未匹配到的类别，返回原英文（避免显示undefined）
      return classMap[className] || className;
    },

    /**
     * 错误提示（适配Element UI和原生alert）
     */
    showError(message) {
      if (this.$message && typeof this.$message.error === 'function') {
        this.$message.error(message);
      } else {
        alert(`错误：${message}`);
      }
    },

    /**
     * 成功提示（适配Element UI和原生alert）
     */
    showSuccess(message) {
      if (this.$message && typeof this.$message.success === 'function') {
        this.$message.success(message);
      } else {
        alert(`成功：${message}`);
      }
    },

    /**
     * 警告提示（适配Element UI和原生alert）
     */
    showWarning(message) {
      if (this.$message && typeof this.$message.warning === 'function') {
        this.$message.warning(message);
      } else {
        alert(`警告：${message}`);
      }
    }
  },
  // 声明自定义事件（父组件可监听）
  emits: ['analysis-complete', 'clear-results'],
  // 组件卸载时释放资源
  beforeUnmount() {
    // 释放所有图片预览地址，避免内存泄漏
    this.images.forEach(image => URL.revokeObjectURL(image.url));
  }
};
</script>

<style scoped>
/* 基础变量（可根据项目主题调整） */
:root {
  --border-radius: 8px;
  --transition: all 0.3s ease;
  --light-bg: #f8f9fa;
  --primary-color: #4285f4;
  --success-color: #34a853;
  --warning-color: #fbbc05;
  --error-color: #ea4335;
  --text-primary: #202124;
  --text-secondary: #5f6368;
}

.upload-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 上传区域样式 */
.upload-area {
  width: 100%;
  border: 2px dashed #d1d8e0;
  border-radius: var(--border-radius);
  padding: 2.5rem;
  text-align: center;
  cursor: pointer;
  transition: var(--transition);
  background: var(--light-bg);
}

.upload-area:hover {
  border-color: var(--primary-color);
  background: rgba(66, 133, 244, 0.05);
}

.upload-icon {
  font-size: 3.5rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
}

.upload-text {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-primary);
}

.upload-hint {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* 连接警告样式 */
.connection-warning {
  margin: 1rem 0;
}

/* 进度条样式 */
.progress-indicator {
  margin: 1rem 0;
  text-align: center;
  color: var(--text-primary);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--success-color), var(--primary-color));
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* 图片列表样式 */
.images-container h3 {
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
}

.image-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: var(--transition);
  background: #fff;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.thumbnail {
  width: 100%;
  height: 100px;
  object-fit: cover;
  display: block;
}

/* 图片覆盖层（删除按钮+文件名） */
.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 0.5rem;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
}

.image-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 0.5rem;
  line-height: 1.2;
}

/* 按钮样式 */
.btn-icon {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: var(--transition);
  padding: 0;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-icon:disabled {
  background: rgba(255, 255, 255, 0.1);
  cursor: not-allowed;
}

.upload-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.btn-secondary {
  background: #e9ecef;
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background: #dde1e6;
}

.btn-secondary:disabled {
  background: #f1f3f5;
  color: #adb5bd;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background: #3367d6;
}

.btn-primary:disabled {
  background: #8ab4f8;
  cursor: not-allowed;
}

/* 加载中动画（简单旋转效果） */
.loading {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 响应式调整（小屏幕优化） */
@media (max-width: 768px) {
  .upload-area {
    padding: 1.5rem;
  }
  
  .upload-icon {
    font-size: 2.5rem;
  }
  
  .images-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
  
  .upload-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>