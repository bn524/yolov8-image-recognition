from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from ultralytics import YOLO
import uvicorn
from ultralytics import YOLO


app = FastAPI()

# 更详细的CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 明确指定前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # 确保所有头部都能被前端访问
)

# 加载ONNX模型
model = YOLO("yolov8n.onnx", task="detect")

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    try:
        # 读取上传的图片
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"error": "无法读取图片文件"}
        
        # 模型推理
        results = model(img)
        
        # 整理结果格式
        detection_data = {
            "boxes": results[0].boxes.xyxy.tolist() if results[0].boxes else [],
            "classes": [results[0].names[int(cls)] for cls in results[0].boxes.cls.tolist()] if results[0].boxes else [],
            "confidences": results[0].boxes.conf.tolist() if results[0].boxes else []
        }
        
        print(f"检测到 {len(detection_data['classes'])} 个对象")
        return detection_data
        
    except Exception as e:
        print(f"处理错误: {str(e)}")
        return {"error": f"处理图片时发生错误: {str(e)}"}

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "YOLOv8后端服务运行正常"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  # 改为0.0.0.0确保外部可访问
        port=8000, 
        reload=True,
        access_log=True
    )