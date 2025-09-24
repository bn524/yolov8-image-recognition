import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 设置页面标题
document.title = "YOLOv5 图像识别系统 - 基于AI的智能视觉识别平台";

// 导入字体图标
const loadFontAwesome = () => {
  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
  document.head.appendChild(link)
  
  const fontLink = document.createElement('link')
  fontLink.rel = 'stylesheet'
  fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
  document.head.appendChild(fontLink)
}

loadFontAwesome()

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')