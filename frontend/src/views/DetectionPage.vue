<template>
  <div class="detection-page">
    <div class="page-header">
      <h1>YOLOv8 图像检测</h1>
      <p>上传图片进行智能目标检测</p>
    </div>

    <div class="detection-container">
      <!-- 上传区域 -->
      <div class="upload-section card">
        <div class="card-header">
          <h3>上传图片</h3>
        </div>
        <div class="card-body">
          <div class="upload-area" 
               @drop="handleDrop"
               @dragover="handleDragOver"
               @click="triggerFileInput"
               :class="{ 'is-dragging': isDragging, 'has-file': selectedFile }">
            <input type="file" 
                   ref="fileInput"
                   @change="handleFileSelect"
                   accept="image/jpeg,image/png,image/jpg" 
                   style="display: none" />
            
            <div v-if="!selectedFile && !isDetecting" class="upload-placeholder">
              <i class="fas fa-cloud-upload-alt"></i>
              <p>点击或拖拽图片到这里</p>
              <span class="upload-hint">支持 JPG、PNG 格式，最大 10MB</span>
            </div>
            
            <div v-else-if="isDetecting" class="detecting-placeholder">
              <i class="fas fa-spinner fa-spin"></i>
              <p>正在检测中...</p>
              <span class="detecting-hint">请稍候，AI正在分析图片</span>
            </div>
            
            <div v-else class="file-preview">
              <img :src="previewUrl" :alt="selectedFile.name" />
              <div class="file-info">
                <div class="filename">{{ selectedFile.name }}</div>
                <div class="filesize">{{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB</div>
              </div>
              <button class="remove-file" @click.stop="removeFile" v-if="!isDetecting">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          
          <div v-if="uploadError" class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            {{ uploadError }}
          </div>
          
          <div class="upload-actions" v-if="selectedFile && !isDetecting">
            <button class="btn btn-primary" @click="startDetection">
              <i class="fas fa-play"></i> 开始检测
            </button>
            <button class="btn btn-outline" @click="removeFile">
              <i class="fas fa-times"></i> 取消
            </button>
          </div>
        </div>
      </div>

      <!-- 检测结果 -->
      <div v-if="detectionResult" class="result-section card">
        <div class="card-header">
          <h3>检测结果</h3>
          <div class="result-stats">
            <span class="objects-count">{{ detectionResult.count }} 个对象</span>
            <span class="inference-time">{{ detectionResult.inference_time?.toFixed(2) || 'N/A' }} ms</span>
          </div>
        </div>
        <div class="card-body">
          <div class="result-container">
            <div class="result-image">
              <img :src="previewUrl" :alt="selectedFile.name" />
              <!-- 检测框覆盖层 -->
              <div class="detection-overlay">
                <div v-for="detection in detectionResult.detections" 
                     :key="detection.id"
                     class="bounding-box"
                     :style="{
                       left: (detection.bbox[0] / detectionResult.image_size[1] * 100) + '%',
                       top: (detection.bbox[1] / detectionResult.image_size[0] * 100) + '%',
                       width: ((detection.bbox[2] - detection.bbox[0]) / detectionResult.image_size[1] * 100) + '%',
                       height: ((detection.bbox[3] - detection.bbox[1]) / detectionResult.image_size[0] * 100) + '%'
                     }">
                  <div class="box-label">{{ detection.class }} ({{ (detection.confidence * 100).toFixed(1) }}%)</div>
                </div>
              </div>
            </div>
            
            <div class="result-details">
              <h4>检测详情</h4>
              <div class="details-grid">
                <div class="detail-item">
                  <label>文件名:</label>
                  <span>{{ selectedFile.name }}</span>
                </div>
                <div class="detail-item">
                  <label>图片尺寸:</label>
                  <span>{{ detectionResult.image_size[1] }} × {{ detectionResult.image_size[0] }} 像素</span>
                </div>
                <div class="detail-item">
                  <label>检测时间:</label>
                  <span>{{ new Date().toLocaleString() }}</span>
                </div>
                <div class="detail-item">
                  <label>推理时间:</label>
                  <span>{{ detectionResult.inference_time?.toFixed(2) || 'N/A' }} 毫秒</span>
                </div>
              </div>
              
              <div class="objects-list">
                <h5>检测到的对象 ({{ detectionResult.count }}个)</h5>
                <div class="objects-table">
                  <div class="table-header">
                    <span>类别</span>
                    <span>置信度</span>
                    <span>位置</span>
                  </div>
                  <div v-for="detection in detectionResult.detections" 
                       :key="detection.id"
                       class="table-row">
                    <span class="class-name">{{ detection.class }}</span>
                    <span class="confidence">{{ (detection.confidence * 100).toFixed(1) }}%</span>
                    <span class="bbox">
                      [{{ detection.bbox[0].toFixed(0) }}, {{ detection.bbox[1].toFixed(0) }}, 
                      {{ detection.bbox[2].toFixed(0) }}, {{ detection.bbox[3].toFixed(0) }}]
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="result-actions">
                <button class="btn btn-outline" @click="downloadResult">
                  <i class="fas fa-download"></i> 下载结果
                </button>
                <button class="btn btn-primary" @click="newDetection">
                  <i class="fas fa-redo"></i> 新的检测
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 服务状态 -->
      <div class="status-section card">
        <div class="card-header">
          <h3>服务状态</h3>
        </div>
        <div class="card-body">
          <div class="status-indicators">
            <div class="status-item" :class="{ online: serviceOnline }">
              <div class="status-dot"></div>
              <span>检测服务: {{ serviceOnline ? '在线' : '离线' }}</span>
            </div>
            <div class="status-item">
              <div class="status-dot online"></div>
              <span>模型: YOLOv8n</span>
            </div>
            <div class="status-item">
              <div class="status-dot online"></div>
              <span>支持 {{ modelClasses.length }} 种对象检测</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'DetectionPage',
  setup() {
    const selectedFile = ref(null)
    const previewUrl = ref('')
    const isDragging = ref(false)
    const isDetecting = ref(false)
    const uploadError = ref('')
    const detectionResult = ref(null)
    const fileInput = ref(null)
    const serviceOnline = ref(false)
    const modelClasses = ref([])

    // 检查服务状态
    const checkServiceStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/')
        serviceOnline.value = true
        
        // 获取模型信息
        const modelInfo = await axios.get('http://localhost:8000/model/info')
        modelClasses.value = modelInfo.data.classes
        
      } catch (error) {
        serviceOnline.value = false
        console.error('服务连接失败:', error)
      }
    }

    // 文件选择处理
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        validateAndSetFile(file)
      }
    }

    // 拖拽处理
    const handleDragOver = (event) => {
      event.preventDefault()
      isDragging.value = true
    }

    const handleDrop = (event) => {
      event.preventDefault()
      isDragging.value = false
      
      const files = event.dataTransfer.files
      if (files.length > 0) {
        validateAndSetFile(files[0])
      }
    }

    // 文件验证和设置
    const validateAndSetFile = (file) => {
      uploadError.value = ''
      
      // 检查文件类型
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
      if (!allowedTypes.includes(file.type)) {
        uploadError.value = '只支持 JPG、PNG 格式的图片'
        return
      }
      
      // 检查文件大小 (10MB)
      if (file.size > 10 * 1024 * 1024) {
        uploadError.value = '文件大小不能超过 10MB'
        return
      }
      
      selectedFile.value = file
      previewUrl.value = URL.createObjectURL(file)
    }

    // 触发文件输入
    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    // 移除文件
    const removeFile = () => {
      selectedFile.value = null
      previewUrl.value = ''
      uploadError.value = ''
      detectionResult.value = null
    }

    // 开始检测
    const startDetection = async () => {
      if (!selectedFile.value || !serviceOnline.value) return
      
      isDetecting.value = true
      uploadError.value = ''
      
      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        
        const response = await axios.post('http://localhost:8000/detect', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 30000
        })
        
        detectionResult.value = response.data
        console.log('检测成功，记录ID:', response.data.record_id)
        
      } catch (error) {
        console.error('检测失败:', error)
        uploadError.value = error.response?.data?.detail || error.message || '检测失败，请重试'
      } finally {
        isDetecting.value = false
      }
    }

    // 下载结果
    const downloadResult = () => {
      if (!detectionResult.value) return
      
      const dataStr = JSON.stringify(detectionResult.value, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `detection_${selectedFile.value.name}_results.json`
      link.click()
      URL.revokeObjectURL(url)
    }

    // 新的检测
    const newDetection = () => {
      removeFile()
    }

    // 初始化
    onMounted(() => {
      checkServiceStatus()
    })

    return {
      selectedFile,
      previewUrl,
      isDragging,
      isDetecting,
      uploadError,
      detectionResult,
      fileInput,
      serviceOnline,
      modelClasses,
      handleFileSelect,
      handleDragOver,
      handleDrop,
      triggerFileInput,
      removeFile,
      startDetection,
      downloadResult,
      newDetection
    }
  }
}
</script>

<style scoped>
.detection-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  color: var(--text-color);
}

.page-header p {
  font-size: 1.1rem;
  color: var(--gray);
}

.detection-container {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

/* 上传区域样式 */
.upload-area {
  border: 2px dashed #ddd;
  border-radius: 12px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
  background: var(--card-bg);
}

.upload-area.is-dragging {
  border-color: var(--primary);
  background: rgba(58, 123, 213, 0.05);
}

.upload-area.has-file {
  border-color: var(--success);
  background: rgba(46, 204, 113, 0.05);
  padding: 30px;
}

.upload-placeholder i,
.detecting-placeholder i {
  font-size: 4rem;
  color: var(--gray);
  margin-bottom: 20px;
}

.upload-placeholder p,
.detecting-placeholder p {
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: var(--text-color);
  font-weight: 500;
}

.upload-hint,
.detecting-hint {
  color: var(--gray);
  font-size: 0.9rem;
}

.detecting-placeholder i {
  color: var(--primary);
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
}

.file-preview img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.file-info {
  flex: 1;
  text-align: left;
}

.filename {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-color);
}

.filesize {
  color: var(--gray);
  font-size: 0.9rem;
}

.remove-file {
  position: absolute;
  top: -10px;
  right: -10px;
  background: var(--danger);
  color: white;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s;
}

.remove-file:hover {
  background: #c0392b;
}

.upload-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

/* 结果区域样式 */
.result-stats {
  display: flex;
  gap: 15px;
  align-items: center;
}

.objects-count {
  background: var(--primary);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.inference-time {
  background: var(--gray);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.result-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.result-image {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #f8f9fa;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-image img {
  width: 100%;
  height: auto;
  display: block;
}

.detection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.bounding-box {
  position: absolute;
  border: 3px solid #ff4757;
  background: rgba(255, 71, 87, 0.1);
  pointer-events: none;
  transition: all 0.3s;
}

.bounding-box:hover {
  background: rgba(255, 71, 87, 0.2);
}

.box-label {
  position: absolute;
  top: -30px;
  left: 0;
  background: #ff4757;
  color: white;
  padding: 4px 8px;
  font-size: 0.8rem;
  border-radius: 4px;
  white-space: nowrap;
  font-weight: 500;
}

.result-details {
  padding: 10px 0;
}

.result-details h4 {
  margin-bottom: 20px;
  color: var(--text-color);
  font-size: 1.3rem;
}

.details-grid {
  display: grid;
  gap: 12px;
  margin-bottom: 25px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.detail-item label {
  font-weight: 600;
  color: var(--text-color);
}

.detail-item span {
  color: var(--gray);
}

.objects-list h5 {
  margin-bottom: 15px;
  color: var(--text-color);
  font-size: 1.1rem;
}

.objects-table {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  background: #f8f9fa;
  padding: 12px 15px;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid #eee;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  padding: 10px 15px;
  border-bottom: 1px solid #eee;
}

.table-row:last-child {
  border-bottom: none;
}

.class-name {
  font-weight: 500;
}

.confidence {
  color: var(--success);
  font-weight: 500;
}

.bbox {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: var(--gray);
}

.result-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
}

/* 状态区域样式 */
.status-indicators {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--danger);
}

.status-dot.online {
  background: var(--success);
}

.error-message {
  background: rgba(231, 76, 60, 0.1);
  border: 1px solid rgba(231, 76, 60, 0.3);
  color: var(--danger);
  padding: 12px 15px;
  border-radius: 6px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 768px) {
  .detection-page {
    padding: 15px;
  }
  
  .result-container {
    grid-template-columns: 1fr;
  }
  
  .file-preview {
    flex-direction: column;
    text-align: center;
  }
  
  .file-info {
    text-align: center;
  }
  
  .upload-actions,
  .result-actions {
    flex-direction: column;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 1fr 1fr;
  }
  
  .bbox {
    display: none;
  }
}
</style>