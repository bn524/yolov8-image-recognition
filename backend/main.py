from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from ultralytics import YOLO
import uvicorn
import logging
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YOLOv8图像识别API",
    description="基于YOLOv8的智能图像识别后端服务",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载YOLOv8模型（使用最新的YOLOv8）
try:
    # 使用YOLOv8n模型（更轻量、更快速）
    model = YOLO("yolov8n.pt")
    logger.info("YOLOv8模型加载成功")
except Exception as e:
    logger.error(f"模型加载失败: {e}")
    raise e

@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "status": "success", 
        "message": "YOLOv8图像识别服务运行正常",
        "version": "2.0.0",
        "model": "yolov8n"
    }

@app.get("/model/info")
async def get_model_info():
    """获取模型信息"""
    return {
        "model_name": "yolov8n",
        "classes": list(model.names.values()),
        "input_size": (640, 640),
        "version": "8.0.0"
    }

@app.post("/detect", response_model=Dict[str, Any])
async def detect_objects(file: UploadFile = File(...)):
    """
    图像目标检测端点
    - 支持格式: JPEG, PNG
    - 最大文件大小: 10MB
    """
    # 验证文件类型
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="不支持的文件格式")
    
    try:
        # 读取图片
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB限制
            raise HTTPException(status_code=400, detail="文件过大")
            
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="无法读取图片")
        
        # 使用YOLOv8进行推理
        results = model(img, verbose=False)  # verbose=False关闭详细输出
        
        # 处理检测结果
        if not results or len(results) == 0:
            return {
                "detections": [],
                "count": 0,
                "image_size": img.shape[:2]
            }
        
        result = results[0]
        detections = []
        
        if result.boxes is not None:
            for i, (box, cls, conf) in enumerate(zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf)):
                detection = {
                    "id": i,
                    "bbox": box.tolist(),  # [x1, y1, x2, y2]
                    "class": model.names[int(cls)],
                    "confidence": float(conf),
                    "class_id": int(cls)
                }
                detections.append(detection)
        
        logger.info(f"检测到 {len(detections)} 个对象")
        
        return {
            "detections": detections,
            "count": len(detections),
            "image_size": img.shape[:2],
            "inference_time": sum(result.speed.values())  # 推理时间(ms)
        }
        
    except Exception as e:
        logger.error(f"检测错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.get("/stats")
async def get_service_stats():
    """获取服务统计信息"""
    return {
        "status": "running",
        "model": "yolov8n",
        "uptime": "待实现",  # 实际项目中可以添加启动时间计算
        "requests_processed": "待实现"  # 实际项目中可以添加请求计数
    }

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )