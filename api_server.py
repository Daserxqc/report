from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import asyncio
import threading
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import traceback

# 导入原有的报告生成功能
from generate_news_report_enhanced import IntelligentReportAgent, generate_news_report

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="智能行业分析报告生成器 API",
    description="基于AI的行业分析报告生成服务，采用五步智能分析法",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域name
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局任务存储
tasks_storage = {}

class ReportRequest(BaseModel):
    """报告生成请求模型"""
    topic: str = Field(..., description="报告主题", example="人工智能")
    companies: Optional[List[str]] = Field(None, description="重点关注的公司列表", example=["OpenAI", "百度"])
    days: int = Field(7, ge=1, le=30, description="搜索时间范围（天）", example=7)
    output_filename: Optional[str] = Field(None, description="输出文件名", example="AI_report.md")

class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ReportResponse(BaseModel):
    """报告响应模型"""
    success: bool
    task_id: str
    message: str
    download_url: Optional[str] = None

def update_task_status(task_id: str, status: str, progress: str = "", result: Dict = None, error: str = None):
    """更新任务状态"""
    if task_id in tasks_storage:
        tasks_storage[task_id].update({
            "status": status,
            "progress": progress,
            "completed_at": datetime.now().isoformat() if status in ["completed", "failed"] else None,
            "result": result,
            "error": error
        })

def generate_report_background(task_id: str, topic: str, companies: List[str] = None, days: int = 7, output_filename: str = None):
    """后台任务：生成报告"""
    try:
        update_task_status(task_id, "running", "🚀 初始化智能分析代理...")
        
        # 创建智能代理
        agent = IntelligentReportAgent()
        
        update_task_status(task_id, "running", "🧠 正在进行智能查询生成...")
        
        # 生成报告
        report_data = agent.generate_comprehensive_report_with_thinking(topic, days, companies)
        
        update_task_status(task_id, "running", "📝 正在生成最终报告文件...")
        
        # 保存报告文件
        if not output_filename:
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_topic = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in topic])
            safe_topic = safe_topic.replace(' ', '_')
            output_filename = f"{safe_topic}_智能分析报告_{date_str}.md"
        
        # 确保reports目录存在
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        file_path = os.path.join(reports_dir, output_filename)
        
        # 保存文件
        with open(file_path, "w", encoding="utf-8-sig") as f:
            f.write(report_data["content"])
        
        # 更新任务完成状态
        result = {
            "file_path": file_path,
            "filename": output_filename,
            "content_preview": report_data["content"][:500] + "..." if len(report_data["content"]) > 500 else report_data["content"],
            "data_summary": {
                "breaking_news": len(report_data["data"].get("breaking_news", [])),
                "innovation_news": len(report_data["data"].get("innovation_news", [])),
                "investment_news": len(report_data["data"].get("investment_news", [])),
                "policy_news": len(report_data["data"].get("policy_news", [])),
                "trend_news": len(report_data["data"].get("trend_news", [])),
                "company_news": len(report_data["data"].get("company_news", []))
            },
            "report_date": report_data["date"]
        }
        
        update_task_status(task_id, "completed", "✅ 报告生成完成", result)
        
    except Exception as e:
        error_msg = f"报告生成失败: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ 任务 {task_id} 失败: {error_msg}")
        update_task_status(task_id, "failed", "❌ 报告生成失败", error=error_msg)

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "智能行业分析报告生成器 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.post("/api/generate-report", response_model=ReportResponse)
async def generate_report_api(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    生成智能行业分析报告
    
    采用AI代理的五步分析法：
    1. 🧠 智能查询生成
    2. 📊 网络信息搜集  
    3. 🤔 反思与知识缺口分析
    4. 🎯 迭代优化搜索
    5. 📝 综合报告生成
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        tasks_storage[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": "📋 任务已创建，等待开始...",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None,
            "error": None,
            "request_data": {
                "topic": request.topic,
                "companies": request.companies,
                "days": request.days,
                "output_filename": request.output_filename
            }
        }
        
        # 添加后台任务
        background_tasks.add_task(
            generate_report_background,
            task_id=task_id,
            topic=request.topic,
            companies=request.companies,
            days=request.days,
            output_filename=request.output_filename
        )
        
        return ReportResponse(
            success=True,
            task_id=task_id,
            message=f"报告生成任务已启动，主题: {request.topic}",
            download_url=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动报告生成任务失败: {str(e)}"
        )

@app.get("/api/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task_info = tasks_storage[task_id]
    return TaskStatus(**task_info)

@app.get("/api/tasks")
async def list_tasks(limit: int = 10):
    """获取任务列表"""
    # 按创建时间倒序排列
    sorted_tasks = sorted(
        tasks_storage.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )
    return {
        "tasks": sorted_tasks[:limit],
        "total": len(tasks_storage)
    }

@app.get("/api/download/{task_id}")
async def download_report(task_id: str):
    """下载生成的报告文件"""
    if task_id not in tasks_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task_info = tasks_storage[task_id]
    
    if task_info["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="报告尚未生成完成"
        )
    
    if not task_info["result"] or "file_path" not in task_info["result"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告文件不存在"
        )
    
    file_path = task_info["result"]["file_path"]
    filename = task_info["result"]["filename"]
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告文件已被删除"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/markdown',
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )

@app.get("/api/preview/{task_id}")
async def preview_report(task_id: str):
    """预览报告内容"""
    if task_id not in tasks_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task_info = tasks_storage[task_id]
    
    if task_info["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="报告尚未生成完成"
        )
    
    if not task_info["result"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告内容不存在"
        )
    
    # 读取完整文件内容
    file_path = task_info["result"]["file_path"]
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            full_content = f.read()
    else:
        full_content = "文件不存在"
    
    return {
        "task_id": task_id,
        "filename": task_info["result"]["filename"],
        "content": full_content,
        "data_summary": task_info["result"]["data_summary"],
        "report_date": task_info["result"]["report_date"]
    }

@app.delete("/api/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务和相关文件"""
    if task_id not in tasks_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task_info = tasks_storage[task_id]
    
    # 删除文件（如果存在）
    if task_info.get("result") and task_info["result"].get("file_path"):
        file_path = task_info["result"]["file_path"]
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除文件失败: {e}")
    
    # 删除任务记录
    del tasks_storage[task_id]
    
    return {"message": "任务已删除"}

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len([t for t in tasks_storage.values() if t["status"] in ["pending", "running"]]),
        "completed_tasks": len([t for t in tasks_storage.values() if t["status"] == "completed"]),
        "failed_tasks": len([t for t in tasks_storage.values() if t["status"] == "failed"])
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动智能报告生成 API 服务器...")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🔧 管理界面: http://localhost:8000/redoc")
    
    print("🌐 局域网IP地址:")
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"   - 本机访问: http://localhost:8000")
    print(f"   - 局域网访问: http://{local_ip}:8000")
    print(f"   - 所有网络: http://0.0.0.0:8000")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",  # 允许所有IP访问
        port=8000,
        reload=True,
        log_level="info"
    ) 