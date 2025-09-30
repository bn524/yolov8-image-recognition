from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import cv2
import numpy as np
from ultralytics import YOLO
import uvicorn
import logging
import json
from typing import List, Dict, Any
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./detections.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 检测记录模型
class DetectionRecord(Base):
    __tablename__ = "detection_records"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    image_size = Column(String)  # 存储为 "width,height"
    detection_count = Column(Integer)
    inference_time = Column(Float)
    detection_results = Column(Text)  # 存储为JSON字符串
    thumbnail_path = Column(String)  # 缩略图路径

# 创建表
Base.metadata.create_all(bind=engine)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="YOLOv8图像识别API",
    description="基于YOLOv8的智能图像识别后端服务",
    version="2.0.0"
)

# CORS配置 - 允许所有前端应用访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建缩略图目录
THUMBNAIL_DIR = "thumbnails"
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# 加载YOLOv8模型
try:
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

def create_thumbnail(image, filename, max_size=(200, 200)):
    """创建缩略图"""
    try:
        # 计算缩放比例
        h, w = image.shape[:2]
        scale = min(max_size[0] / w, max_size[1] / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # 缩放图像
        thumbnail = cv2.resize(image, (new_w, new_h))
        
        # 保存缩略图
        thumbnail_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        thumbnail_path = os.path.join(THUMBNAIL_DIR, thumbnail_filename)
        cv2.imwrite(thumbnail_path, thumbnail)
        
        return thumbnail_path
    except Exception as e:
        logger.error(f"创建缩略图失败: {e}")
        return None

@app.post("/detect", response_model=Dict[str, Any])
async def detect_objects(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
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
        
        # 创建缩略图
        thumbnail_path = create_thumbnail(img, file.filename)
        
        # 使用YOLOv8进行推理
        results = model(img, verbose=False)
        
        # 处理检测结果
        if not results or len(results) == 0:
            # 即使没有检测到对象也要保存记录
            detection_record = DetectionRecord(
                filename=file.filename,
                image_size=f"{img.shape[1]},{img.shape[0]}",
                detection_count=0,
                inference_time=0,
                detection_results=json.dumps([]),
                thumbnail_path=thumbnail_path
            )
            db.add(detection_record)
            db.commit()
            
            return {
                "detections": [],
                "count": 0,
                "image_size": img.shape[:2],
                "inference_time": 0,
                "record_id": detection_record.id
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
        
        inference_time = sum(result.speed.values()) if result.speed else 0
        
        # 保存检测记录到数据库
        detection_record = DetectionRecord(
            filename=file.filename,
            image_size=f"{img.shape[1]},{img.shape[0]}",
            detection_count=len(detections),
            inference_time=inference_time,
            detection_results=json.dumps(detections),
            thumbnail_path=thumbnail_path
        )
        db.add(detection_record)
        db.commit()
        
        logger.info(f"检测到 {len(detections)} 个对象，记录ID: {detection_record.id}")
        
        return {
            "detections": detections,
            "count": len(detections),
            "image_size": img.shape[:2],
            "inference_time": inference_time,
            "record_id": detection_record.id
        }
        
    except Exception as e:
        logger.error(f"检测错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.get("/detections")
async def get_detection_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取检测历史记录"""
    records = db.query(DetectionRecord).order_by(DetectionRecord.upload_time.desc()).offset(skip).limit(limit).all()
    
    result = []
    for record in records:
        # 构建缩略图URL
        thumbnail_url = f"/thumbnails/{os.path.basename(record.thumbnail_path)}" if record.thumbnail_path else None
        
        result.append({
            "id": record.id,
            "filename": record.filename,
            "upload_time": record.upload_time.isoformat(),
            "image_size": record.image_size,
            "detection_count": record.detection_count,
            "inference_time": record.inference_time,
            "detection_results": json.loads(record.detection_results) if record.detection_results else [],
            "thumbnail_url": thumbnail_url
        })
    
    return {
        "records": result,
        "total": db.query(DetectionRecord).count(),
        "skip": skip,
        "limit": limit
    }

@app.get("/detections/{record_id}")
async def get_detection_detail(record_id: int, db: Session = Depends(get_db)):
    """获取特定检测记录的详细信息"""
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    thumbnail_url = f"/thumbnails/{os.path.basename(record.thumbnail_path)}" if record.thumbnail_path else None
    
    return {
        "id": record.id,
        "filename": record.filename,
        "upload_time": record.upload_time.isoformat(),
        "image_size": record.image_size,
        "detection_count": record.detection_count,
        "inference_time": record.inference_time,
        "detection_results": json.loads(record.detection_results) if record.detection_results else [],
        "thumbnail_url": thumbnail_url
    }

# 静态文件服务 - 提供缩略图访问
from fastapi.staticfiles import StaticFiles
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")

@app.get("/stats")
async def get_service_stats(db: Session = Depends(get_db)):
    """获取服务统计信息"""
    total_detections = db.query(DetectionRecord).count()
    today = datetime.utcnow().date()
    today_detections = db.query(DetectionRecord).filter(
        DetectionRecord.upload_time >= datetime(today.year, today.month, today.day)
    ).count()
    
    return {
        "status": "running",
        "model": "yolov8n",
        "total_detections": total_detections,
        "today_detections": today_detections,
        "detection_categories": len(model.names)
    }

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )