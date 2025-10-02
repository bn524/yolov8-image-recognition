<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>联系我们</h2>
        <button class="modal-close" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div class="contact-info">
          <div class="contact-item">
            <div class="contact-icon">
              <i class="fas fa-user"></i>
            </div>
            <div class="contact-details">
              <h3>作者</h3>
              <p>谁寄奈归云</p>
            </div>
          </div>
          
          <div class="contact-item">
            <div class="contact-icon">
              <i class="fas fa-envelope"></i>
            </div>
            <div class="contact-details">
              <h3>邮箱</h3>
              <p>SentCloud4@163.com</p>
            </div>
          </div>
          
          <div class="contact-item">
            <div class="contact-icon">
              <i class="fas fa-phone"></i>
            </div>
            <div class="contact-details">
              <h3>电话</h3>
              <p>+86 180 8069 4763</p>
            </div>
          </div>
          
          <div class="contact-item">
            <div class="contact-icon">
              <i class="fab fa-github"></i>
            </div>
            <div class="contact-details">
              <h3>GitHub</h3>
              <a href="https://github.com/bn524" target="_blank">github.com/bn524</a>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary" @click="$emit('close')">
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContactModal',
  emits: ['close']
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0.25rem;
  border-radius: 4px;
  transition: var(--transition);
}

.modal-close:hover {
  background: #f5f5f5;
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.contact-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--light-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  font-size: 1.25rem;
}

.contact-details h3 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  color: var(--text-primary);
}

.contact-details p,
.contact-details a {
  margin: 0;
  color: var(--text-secondary);
  text-decoration: none;
}

.contact-details a:hover {
  color: var(--primary-color);
  text-decoration: underline;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e9ecef;
  text-align: right;
}
</style>