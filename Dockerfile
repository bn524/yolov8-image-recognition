# 第一阶段：安装依赖（只保留构建必需品，减小体积）
FROM python:3.10-slim AS builder
WORKDIR /app

# 复制后端依赖文件（只复制requirements.txt，利用Docker缓存）
COPY requirements.txt .

# 用清华源安装依赖+清理缓存（关键！减少几百MB）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && rm -rf /root/.cache/pip  # 删除pip安装缓存

# 第二阶段：运行环境（只复制必要文件，体积最小）
FROM python:3.10-slim
WORKDIR /app

# 复制第一阶段安装好的依赖（避免重复安装，节省空间）
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# 复制后端核心代码（只复制后端文件，前端已被.dockerignore排除）
# 如果你有其他后端文件夹（如routes/、utils/），按此格式添加
COPY main.py .                 
COPY models/ ./models/        
COPY api/ ./api/              
COPY utils/ ./utils/       

# 启动命令：先下载YOLOv8模型（用n版，体积最小，适合部署），再启动服务
# 模型链接可替换：n(小)→s→m→l→x(大)，根据需求选择
CMD ["sh", "-c", \
     "wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt -O yolov8n.pt && \
      python main.py"]
    