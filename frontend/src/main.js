import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

// 加载字体图标
const loadFonts = () => {
  const fontAwesome = document.createElement('link')
  fontAwesome.rel = 'stylesheet'
  fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
  document.head.appendChild(fontAwesome)
  
  const googleFont = document.createElement('link')
  googleFont.rel = 'stylesheet'
  googleFont.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
  document.head.appendChild(googleFont)
}

loadFonts()

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')