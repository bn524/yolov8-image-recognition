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
          :disabled="!hasImages || analyzing"
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
          <p class="upload-hint">支持 JPG, PNG 格式，可多选，最大10MB/张</p>
          <input 
            type="file" 
            ref="fileInput" 
            @change="handleFileUpload" 
            accept="image/*" 
            multiple 
            hidden
          >
        </div>

        <div v-if="!backendConnected" class="connection-warning">
          <el-alert title="后端连接异常" type="warning" show-icon :closable="false">
            <p>无法连接到YOLOv8检测服务，请确保后端服务正在运行在 http://localhost:8000</p>
            <button class="btn btn-small" @click="checkBackendConnection">重试连接</button>
          </el-alert>
        </div>

        <div v-if="analyzing" class="progress-indicator">
          <el-progress 
            :percentage="progressPercentage" 
            :stroke-width="8" 
            status="success"
            :show-text="false"
          />
          <p>正在分析第 {{ currentAnalyzingIndex + 1 }} 张图片，共 {{ images.length }} 张</p>
          <p class="progress-detail">检测到 {{ currentDetectionCount }} 个对象</p>
        </div>

        <div v-if="images.length > 0" class="images-container">
          <h3>已选择 {{ images.length }} 张图片</h3>
          <div class="images-grid">
            <div v-for="(image, index) in images" :key="image.id" class="image-item">
              <img :src="image.url" :alt="`Preview ${index + 1}`" class="thumbnail">
              <div class="image-overlay">
                <button class="btn-icon" @click="removeImage(index)" :disabled="analyzing">
                  <i class="fas fa-times"></i>
                </button>
                <span class="image-name">{{ image.file.name }}</span>
                <span v-if="image.status" class="image-status" :class="image.status">
                  {{ image.status === 'analyzing' ? '分析中' : '已完成' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { inject } from 'vue'

// 注入全局方法
const handleAnalysisComplete = inject('handleAnalysisComplete')

// 响应式数据
const images = ref([])
const analyzing = ref(false)
const currentAnalyzingIndex = ref(0)
const backendConnected = ref(true)
const currentDetectionCount = ref(0)

// 计算属性
const hasImages = computed(() => images.value.length > 0)
const progressPercentage = computed(() => {
  return images.value.length > 0 
    ? Math.round(((currentAnalyzingIndex.value + 1) / images.value.length) * 100) 
    : 0
})

// API配置
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/detect'

// 组件挂载时检查后端连接
onMounted(() => {
  checkBackendConnection()
})

// 方法
const triggerFileInput = () => {
  document.getElementById('fileInput')?.click() || fileInput.value?.click()
}

const fileInput = ref(null)

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files)
  if (files.length === 0) return
  addImages(files)
}

const handleDrop = (event) => {
  event.preventDefault()
  const files = Array.from(event.dataTransfer.files).filter(file => 
    file.type.startsWith('image/')
  )
  if (files.length > 0) {
    addImages(files)
  }
}

const addImages = (files) => {
  files.forEach(file => {
    if (!file.type.startsWith('image/')) return
    
    // 检查文件大小
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.error(`文件 ${file.name} 太大，请选择小于10MB的图片`)
      return
    }
    
    // 检查是否已存在同名文件
    const exists = images.value.some(img => img.file.name === file.name)
    if (exists) {
      ElMessage.warning(`文件 ${file.name} 已存在`)
      return
    }
    
    images.value.push({
      id: Date.now() + Math.random(),
      file,
      url: URL.createObjectURL(file),
      status: null
    })
  })
}

const removeImage = (index) => {
  URL.revokeObjectURL(images.value[index].url)
  images.value.splice(index, 1)
}

const clearAll = async () => {
  if (analyzing.value) {
    ElMessage.warning('请等待分析完成后再清除')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要清除所有图片吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    images.value.forEach(image => URL.revokeObjectURL(image.url))
    images.value = []
    if (fileInput.value) fileInput.value.value = ''
    
    ElMessage.success('已清除所有图片')
  } catch {
    // 用户取消操作
  }
}

const analyzeAll = async () => {
  if (images.value.length === 0 || !backendConnected.value) return
  
  analyzing.value = true
  let successCount = 0
  let errorCount = 0
  
  for (let i = 0; i < images.value.length; i++) {
    currentAnalyzingIndex.value = i
    images.value[i].status = 'analyzing'
    
    try {
      await analyzeImage(images.value[i])
      successCount++
      images.value[i].status = 'completed'
    } catch (error) {
      console.error(`分析第 ${i + 1} 张图片失败:`, error)
      errorCount++
      images.value[i].status = 'error'
    }
    
    // 添加延迟避免请求过于密集
    if (i < images.value.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 300))
    }
  }
  
  analyzing.value = false
  currentAnalyzingIndex.value = 0
  
  if (errorCount === 0) {
    ElMessage.success(`成功分析 ${successCount} 张图片`)
  } else {
    ElMessage.warning(`分析完成。成功 ${successCount} 张，失败 ${errorCount} 张`)
  }
}

const analyzeImage = async (image) => {
  try {
    const formData = new FormData()
    formData.append('file', image.file)

    const response = await fetch(apiUrl, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(60000) // 60秒超时
    })

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`)
    }

    const data = await response.json()
    
    // 更新当前检测数量显示
    currentDetectionCount.value = data.count || 0
    
    // 转换数据格式
    const detections = transformDetectionData(data)
    
    const result = {
      detections,
      imageUrl: image.url,
      fileName: image.file.name,
      inferenceTime: data.inference_time || 0,
      imageSize: data.image_size || [0, 0]
    }

    handleAnalysisComplete(result)
    
  } catch (error) {
    if (error.name === 'TimeoutError') {
      throw new Error('请求超时，请检查后端服务')
    } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
      backendConnected.value = false
      throw new Error('无法连接到检测服务')
    } else {
      throw error
    }
  }
}

const transformDetectionData = (backendData) => {
  const detections = []
  
  if (backendData.detections && Array.isArray(backendData.detections)) {
    backendData.detections.forEach(detection => {
      const [x1, y1, x2, y2] = detection.bbox
      detections.push({
        class: translateClass(detection.class),
        confidence: detection.confidence,
        bbox: [x1, y1, x2 - x1, y2 - y1],
        classId: detection.class_id
      })
    })
  }
  
  return detections
}

const translateClass = (className) => {
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
  }
  
  return classMap[className] || className
}

const checkBackendConnection = async () => {
  try {
    const response = await fetch(apiUrl.replace('/detect', ''), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    backendConnected.value = response.ok
    if (response.ok) {
      const data = await response.json()
      console.log('后端服务信息:', data)
    }
  } catch (error) {
    console.error('后端连接检查失败:', error)
    backendConnected.value = false
  }
}

// 监听analyzing状态变化
watch(analyzing, (newVal) => {
  if (!newVal) {
    currentDetectionCount.value = 0
  }
})
</script>

<style scoped>
/* 样式保持不变，与之前相同 */
.upload-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

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
  background: rgba(67, 97, 238, 0.05);
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
}

.upload-hint {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.connection-warning {
  margin: 1rem 0;
}

.progress-indicator {
  margin: 1rem 0;
  text-align: center;
}

.progress-detail {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-top: 0.5rem;
}

.images-container h3 {
  margin-bottom: 1rem;
  color: var(--text-primary);
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
  flex-wrap: wrap;
}

.image-name {
  font-size: 0.7rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 0.5rem;
}

.image-status {
  font-size: 0.6rem;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.2);
}

.image-status.analyzing {
  background: var(--warning-color);
}

.image-status.completed {
  background: var(--success-color);
}

.image-status.error {
  background: var(--warning-color);
}

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
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-actions {
  display: flex;
  gap: 0.5rem;
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

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(67, 97, 238, 0.4);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: white;
  color: var(--text-primary);
  border: 1px solid #d1d8e0;
}

.btn-secondary:hover:not(:disabled) {
  background: #f8f9fa;
}

.btn-secondary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-small {
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
}

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
  to { transform: rotate(360deg); }
}
</style>