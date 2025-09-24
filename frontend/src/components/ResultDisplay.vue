<template>
  <div class="card result-card">
    <div class="card-header">
      <h3 class="card-title">{{ results.fileName }}</h3>
      <button class="btn-icon" @click="$emit('remove-result')">
        <i class="fas fa-times"></i>
      </button>
    </div>
    <div class="card-body">
      <div class="result-content">
        <div class="image-with-canvas">
          <canvas ref="canvas" class="detection-canvas"></canvas>
        </div>
        <div class="result-details">
          <h4>检测结果 ({{ results.detections.length }}个对象)</h4>
          <div class="detections-list">
            <div v-for="(detection, index) in results.detections" :key="index" class="detection-item">
              <div class="detection-class">
                <span class="class-badge" :style="{ backgroundColor: getColor(index) }"></span>
                {{ detection.class }}
              </div>
              <div class="detection-confidence">
                <div class="confidence-value">{{ (detection.confidence * 100).toFixed(1) }}%</div>
                <div class="confidence-bar">
                  <div 
                    class="confidence-level" 
                    :style="{ 
                      width: detection.confidence * 100 + '%',
                      backgroundColor: getColor(index)
                    }"
                  ></div>
                </div>
              </div>
              <div class="detection-bbox">
                X:{{ Math.round(detection.bbox[0]) }}, Y:{{ Math.round(detection.bbox[1]) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ResultDisplay',
  props: {
    results: {
      type: Object,
      required: true
    }
  },
  mounted() {
    this.drawBoxes()
  },
  methods: {
    drawBoxes() {
      if (!this.$refs.canvas || !this.results.imageUrl) return
      
      const ctx = this.$refs.canvas.getContext('2d')
      const img = new Image()
      
      img.onload = () => {
        // 设置canvas尺寸与图片一致
        this.$refs.canvas.width = img.width
        this.$refs.canvas.height = img.height
        
        // 绘制原图
        ctx.drawImage(img, 0, 0, img.width, img.height)
        
        // 定义颜色数组
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#F9C80E', '#FF6B6B', '#4ECDC4']
        
        // 绘制检测框和标签
        this.results.detections.forEach((det, index) => {
          const [x, y, width, height] = det.bbox
          const color = colors[index % colors.length]
          
          // 绘制检测框
          ctx.lineWidth = 3
          ctx.strokeStyle = color
          ctx.beginPath()
          ctx.rect(x, y, width, height)
          ctx.stroke()
          
          // 绘制标签背景
          ctx.font = 'bold 14px Inter'
          const label = `${det.class} ${(det.confidence * 100).toFixed(1)}%`
          const textWidth = ctx.measureText(label).width
          
          ctx.fillStyle = color
          ctx.fillRect(x, y - 18, textWidth + 10, 18)
          
          // 绘制标签文字
          ctx.fillStyle = 'white'
          ctx.fillText(label, x + 5, y - 5)
        })
      }
      
      img.src = this.results.imageUrl
    },
    getColor(index) {
      const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#F9C80E', '#FF85C0', '#9254DE']
      return colors[index % colors.length]
    }
  },
  emits: ['remove-result']
}
</script>

<style scoped>
.result-card {
  height: fit-content;
}

.result-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.image-with-canvas {
  display: flex;
  justify-content: center;
}

.detection-canvas {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-details h4 {
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.detections-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detection-item {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 0.5rem;
  align-items: center;
  padding: 0.5rem;
  background: var(--light-bg);
  border-radius: 6px;
}

.detection-class {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.class-badge {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.detection-confidence {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.confidence-value {
  font-size: 0.8rem;
  font-weight: 600;
}

.confidence-bar {
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.confidence-level {
  height: 100%;
  border-radius: 3px;
}

.detection-bbox {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.btn-icon {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: var(--transition);
}

.btn-icon:hover {
  background: #f5f5f5;
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .result-content {
    grid-template-columns: 1fr;
  }
  
  .detection-item {
    grid-template-columns: 1fr;
    text-align: center;
  }
}
</style>