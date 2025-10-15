from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, func
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
import uuid
from contextlib import asynccontextmanager
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway 环境变量配置
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./detections.db")
PORT = int(os.environ.get("PORT", 8000))

# 如果是 Railway 的 PostgreSQL 数据库，需要调整连接字符串
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 数据库配置
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 检测记录模型
class DetectionRecord(Base):
    __tablename__ = "detection_records"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    image_size = Column(String)  # 存储为 "width,height"
    detection_count = Column(Integer, default=0)  # 检测到的对象数量
    inference_time = Column(Float, default=0.0)
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

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("🚀 YOLOv8 API 服务启动中...")
    
    # 确保缩略图目录存在
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    
    # 预加载模型
    global model
    try:
        model = YOLO("yolov8n.pt")
        logger.info("✅ YOLOv8模型加载成功")
    except Exception as e:
        logger.error(f"❌ 模型加载失败: {e}")
        raise e
    
    yield  # 应用运行期间
    
    # 关闭时执行
    logger.info("🛑 服务关闭中...")

app = FastAPI(
    title="YOLOv8图像识别API",
    description="基于YOLOv8的智能图像识别后端服务",
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置 - 允许所有前端应用访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Railway 部署允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 使用临时目录存储缩略图（Railway 的持久化存储有限）
THUMBNAIL_DIR = os.path.join(tempfile.gettempdir(), "yolo_thumbnails")
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# 全局模型变量
model = None

@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "status": "success", 
        "message": "YOLOv8图像识别服务运行正常",
        "version": "2.0.0",
        "model": "yolov8n",
        "environment": "production" if DATABASE_URL != "sqlite:///./detections.db" else "development"
    }

@app.get("/health")
async def health_check():
    """更详细的健康检查"""
    try:
        # 测试数据库连接
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # 测试模型
        if model is None:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": "模型未加载"}
            )
        
        return {
            "status": "healthy",
            "database": "connected",
            "model": "loaded",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/model/info")
async def get_model_info():
    """获取模型信息"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    return {
        "model_name": "yolov8n",
        "classes": list(model.names.values()),
        "input_size": (640, 640),
        "version": "8.0.0",
        "class_count": len(model.names)
    }

def create_thumbnail(image, filename, max_size=(200, 200)):
    """创建缩略图"""
    try:
        # 生成唯一文件名
        file_ext = os.path.splitext(filename)[1] or '.jpg'
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
        thumbnail_path = os.path.join(THUMBNAIL_DIR, unique_filename)
        
        # 计算缩放比例
        h, w = image.shape[:2]
        scale = min(max_size[0] / w, max_size[1] / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # 缩放图像
        thumbnail = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # 保存缩略图
        success = cv2.imwrite(thumbnail_path, thumbnail)
        if not success:
            logger.error(f"缩略图保存失败: {thumbnail_path}")
            return None
            
        logger.info(f"缩略图创建成功: {thumbnail_path}")
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
    if model is None:
        raise HTTPException(status_code=503, detail="模型服务暂不可用")
    
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，仅支持: {', '.join(allowed_types)}")
    
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
        start_time = datetime.now()
        results = model(img, verbose=False)
        inference_time = (datetime.now() - start_time).total_seconds() * 1000  # 转换为毫秒
        
        # 处理检测结果
        detections = []
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for i, (box, cls, conf) in enumerate(zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf)):
                    detection = {
                        "id": i,
                        "bbox": [round(float(x), 2) for x in box.tolist()],  # [x1, y1, x2, y2]
                        "class": model.names[int(cls)],
                        "confidence": round(float(conf), 4),
                        "class_id": int(cls)
                    }
                    detections.append(detection)
        
        detection_count = len(detections)
        
        # 保存检测记录到数据库
        detection_record = DetectionRecord(
            filename=file.filename,
            image_size=f"{img.shape[1]},{img.shape[0]}",
            detection_count=detection_count,
            inference_time=inference_time,
            detection_results=json.dumps(detections, ensure_ascii=False),
            thumbnail_path=thumbnail_path
        )
        db.add(detection_record)
        db.commit()
        db.refresh(detection_record)
        
        logger.info(f"检测到 {detection_count} 个对象，记录ID: {detection_record.id}")
        
        return {
            "status": "success",
            "detections": detections,
            "count": detection_count,
            "image_size": [img.shape[1], img.shape[0]],  # [width, height]
            "inference_time": round(inference_time, 2),
            "record_id": detection_record.id
        }
        
    except Exception as e:
        logger.error(f"检测错误: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.get("/detections")
async def get_detection_history(
    skip: int = 0,
    limit: int = 20,  # Railway 内存有限，减少默认返回数量
    db: Session = Depends(get_db)
):
    """获取检测历史记录"""
    try:
        records = db.query(DetectionRecord).order_by(DetectionRecord.upload_time.desc()).offset(skip).limit(limit).all()
        
        result = []
        for record in records:
            # 构建缩略图URL
            thumbnail_url = None
            if record.thumbnail_path and os.path.exists(record.thumbnail_path):
                thumbnail_filename = os.path.basename(record.thumbnail_path)
                thumbnail_url = f"/thumbnails/{thumbnail_filename}"
            
            # 解析检测结果
            detection_results = []
            if record.detection_results:
                try:
                    detection_results = json.loads(record.detection_results)
                except json.JSONDecodeError:
                    detection_results = []
            
            result.append({
                "id": record.id,
                "filename": record.filename,
                "upload_time": record.upload_time.isoformat() if record.upload_time else None,
                "image_size": record.image_size,
                "detection_count": record.detection_count or 0,
                "inference_time": record.inference_time or 0.0,
                "detection_results": detection_results,
                "thumbnail_url": thumbnail_url
            })
        
        total_count = db.query(DetectionRecord).count()
        
        return {
            "status": "success",
            "records": result,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"获取检测历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取检测历史失败")

@app.get("/detections/{record_id}")
async def get_detection_detail(record_id: int, db: Session = Depends(get_db)):
    """获取特定检测记录的详细信息"""
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 构建缩略图URL
    thumbnail_url = None
    if record.thumbnail_path and os.path.exists(record.thumbnail_path):
        thumbnail_filename = os.path.basename(record.thumbnail_path)
        thumbnail_url = f"/thumbnails/{thumbnail_filename}"
    
    # 解析检测结果
    detection_results = []
    if record.detection_results:
        try:
            detection_results = json.loads(record.detection_results)
        except json.JSONDecodeError:
            detection_results = []
    
    return {
        "id": record.id,
        "filename": record.filename,
        "upload_time": record.upload_time.isoformat() if record.upload_time else None,
        "image_size": record.image_size,
        "detection_count": record.detection_count or 0,
        "inference_time": record.inference_time or 0.0,
        "detection_results": detection_results,
        "thumbnail_url": thumbnail_url
    }

# 静态文件服务 - 提供缩略图访问
from fastapi.staticfiles import StaticFiles
app.mount("/thumbnails", StaticFiles(directory=THUMBNAIL_DIR), name="thumbnails")

@app.get("/stats")
async def get_service_stats(db: Session = Depends(get_db)):
    """获取服务统计信息"""
    try:
        total_detections = db.query(DetectionRecord).count()
        
        # 计算今日检测次数
        today = datetime.utcnow().date()
        today_detections = db.query(DetectionRecord).filter(
            func.date(DetectionRecord.upload_time) == today
        ).count()
        
        # 计算总检测对象数量
        total_objects = db.query(func.sum(DetectionRecord.detection_count)).scalar() or 0
        
        return {
            "status": "success",
            "model": "yolov8n",
            "total_detections": total_detections,  # 总检测次数
            "total_objects": int(total_objects),   # 总检测对象数量
            "today_detections": today_detections,  # 今日检测次数
            "detection_categories": len(model.names) if model else 0
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

@app.get("/thumbnails/{filename}")
async def get_thumbnail(filename: str):
    """获取缩略图"""
    thumbnail_path = os.path.join(THUMBNAIL_DIR, filename)
    if not os.path.exists(thumbnail_path):
        raise HTTPException(status_code=404, detail="缩略图不存在")
    return FileResponse(thumbnail_path)

# Railway 特定启动方式
if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # 修改为模块引用方式
        host="0.0.0.0", 
        port=PORT,
        log_level="info",
        reload=False  # 生产环境关闭热重载
    )