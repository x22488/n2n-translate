from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import torch
import os
import pathlib
from fastapi.security import OAuth2PasswordBearer
import secrets
from typing import Optional
import io
import uuid
import shutil
from datetime import datetime

# 获取当前文件的绝对路径
current_file = pathlib.Path(__file__).resolve()
# 获取app目录的绝对路径
app_dir = current_file.parent
# 获取静态文件目录的绝对路径
static_dir = app_dir / "static"

# 创建FastAPI应用
app = FastAPI(title="多语言翻译服务")

# 挂载静态文件 - 必须在创建应用后挂载
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(app_dir / "templates"))

# 全局变量，用于存储模型和分词器
tokenizer = None
model = None

# 模拟用户数据库
fake_users_db = {
    "admin": {
        "username": "admin",
        "password": "123456",
        "display_name": "管理员"
    },
    "user": {
        "username": "user",
        "password": "123456",
        "display_name": "普通用户"
    }
}

# 简单的会话管理
active_sessions = {}

# 支持的语言列表
LANGUAGES = {
    "ar": "阿拉伯语",
    "cs": "捷克语",
    "de": "德语",
    "en": "英语",
    "es": "西班牙语",
    "et": "爱沙尼亚语",
    "fi": "芬兰语",
    "fr": "法语",
    "gu": "古吉拉特语",
    "hi": "印地语",
    "it": "意大利语",
    "ja": "日语",
    "kk": "哈萨克语",
    "ko": "韩语",
    "lt": "立陶宛语",
    "lv": "拉脱维亚语",
    "my": "缅甸语",
    "ne": "尼泊尔语",
    "nl": "荷兰语",
    "ro": "罗马尼亚语",
    "ru": "俄语",
    "si": "僧伽罗语",
    "tr": "土耳其语",
    "vi": "越南语",
    "zh": "中文",
    "af": "南非语",
    "az": "阿塞拜疆语",
    "bn": "孟加拉语",
    "fa": "波斯语",
    "he": "希伯来语",
    "hr": "克罗地亚语",
    "id": "印尼语",
    "ka": "格鲁吉亚语",
    "km": "高棉语",
    "mk": "马其顿语",
    "ml": "马拉雅拉姆语",
    "mn": "蒙古语",
    "mr": "马拉地语",
    "pl": "波兰语",
    "ps": "普什图语",
    "pt": "葡萄牙语",
    "sv": "瑞典语",
    "sw": "斯瓦希里语",
    "ta": "泰米尔语",
    "te": "泰卢固语",
    "th": "泰语",
    "tl": "他加禄语",
    "uk": "乌克兰语",
    "ur": "乌尔都语",
    "xh": "科萨语",
    "gl": "加利西亚语",
    "sl": "斯洛文尼亚语",
    "am": "阿姆哈拉语",
    "ast": "阿斯图里亚斯语",
    "ba": "巴什基尔语",
    "be": "白俄罗斯语",
    "bg": "保加利亚语",
    "br": "布列塔尼语",
    "bs": "波斯尼亚语",
    "ca": "加泰罗尼亚语",
    "ceb": "宿务语",
    "cy": "威尔士语",
    "da": "丹麦语",
    "el": "希腊语",
    "ff": "富拉语",
    "fy": "弗里西语",
    "ga": "爱尔兰语",
    "gd": "苏格兰盖尔语",
    "ha": "豪萨语",
    "ht": "海地克里奥尔语",
    "hu": "匈牙利语",
    "hy": "亚美尼亚语",
    "ig": "伊博语",
    "ilo": "伊洛卡诺语",
    "is": "冰岛语",
    "jv": "爪哇语",
    "lb": "卢森堡语",
    "lg": "卢干达语",
    "ln": "林加拉语",
    "lo": "老挝语",
    "mg": "马达加斯加语",
    "ms": "马来语",
    "no": "挪威语",
    "ns": "北索托语",
    "oc": "奥克语",
    "or": "奥里亚语",
    "pa": "旁遮普语",
    "sd": "信德语",
    "sk": "斯洛伐克语",
    "so": "索马里语",
    "sq": "阿尔巴尼亚语",
    "sr": "塞尔维亚语",
    "ss": "斯威士语",
    "su": "巽他语",
    "wo": "沃洛夫语",
    "yi": "意第绪语",
    "yo": "约鲁巴语",
    "zu": "祖鲁语"
}

class TranslateRequest(BaseModel):
    text: str
    src_lang: str
    tgt_lang: str

class LoginForm(BaseModel):
    username: str
    password: str

# 验证用户会话
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return None
    return active_sessions[session_id]

# 登录页面路由
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    # 检查用户是否已登录
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "error": error}
    )

# 处理登录请求
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # 验证用户凭据
    if username in fake_users_db and fake_users_db[username]["password"] == password:
        # 创建会话
        session_id = secrets.token_hex(16)
        active_sessions[session_id] = fake_users_db[username]
        
        # 创建响应
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    
    # 登录失败，返回登录页面并显示错误信息
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "error": "用户名或密码错误"}
    )

# 注销路由
@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session_id")
    return response

@app.on_event("startup")
async def startup_event():
    """应用启动时加载模型"""
    global tokenizer, model
    try:
        # 获取绝对路径
        model_path = os.path.abspath("./model")
        print(f"正在加载本地模型: {model_path}...")
        
        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            print(f"错误: 模型路径不存在: {model_path}")
            return
        
        # 加载分词器和模型
        print("正在加载分词器...")
        tokenizer = M2M100Tokenizer.from_pretrained(model_path)
        print("分词器加载完成，正在加载模型...")
        model = M2M100ForConditionalGeneration.from_pretrained(model_path)
        
        # 如果有GPU，使用GPU加速
        if torch.cuda.is_available():
            model = model.to("cuda")
            print("使用GPU加速模型")
        else:
            print("使用CPU运行模型")
        
        print("模型加载完成!")
    except Exception as e:
        print(f"模型加载失败: {str(e)}")
        raise

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """返回主页"""
    # 检查用户是否已登录
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "languages": LANGUAGES, "user": user}
    )

@app.post("/translate")
async def translate(req: TranslateRequest):
    """翻译API"""
    try:
        # 设置源语言
        src_lang = req.src_lang.split("_")[0]
        tgt_lang = req.tgt_lang.split("_")[0]
        
        # 编码输入文本
        tokenizer.src_lang = src_lang
        encoded = tokenizer(req.text, return_tensors="pt", max_length=512, truncation=True)
        
        # 如果有GPU，将输入移至GPU
        if torch.cuda.is_available():
            encoded = {k: v.to("cuda") for k, v in encoded.items()}
        
        # 生成翻译
        generated_tokens = model.generate(
            **encoded,
            forced_bos_token_id=tokenizer.get_lang_id(tgt_lang),
            max_length=512,
            num_beams=5,
            early_stopping=True
        )
        
        # 解码翻译结果
        translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        
        return {"translation": translation, "success": True}
    except Exception as e:
        return {"translation": f"翻译出错: {str(e)}", "success": False}

# 创建上传目录
upload_dir = app_dir / "uploads"
os.makedirs(upload_dir, exist_ok=True)

# 创建下载目录
download_dir = app_dir / "downloads"
os.makedirs(download_dir, exist_ok=True)

class BatchTranslateRequest(BaseModel):
    src_lang: str
    tgt_lang: str
    file_id: str

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """处理文件上传"""
    try:
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        
        # 保存上传的文件
        file_path = os.path.join(upload_dir, f"{file_id}{file_extension}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"success": True, "file_id": file_id, "original_filename": file.filename, "file_extension": file_extension}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/batch-translate")
async def batch_translate(req: BatchTranslateRequest):
    """批量翻译API"""
    try:
        # 查找文件
        file_id = req.file_id
        file_path = None
        
        # 查找上传目录中匹配的文件
        for filename in os.listdir(upload_dir):
            if filename.startswith(file_id):
                file_path = os.path.join(upload_dir, filename)
                break
                
        if not file_path:
            return {"success": False, "error": "找不到上传的文件"}
            
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 按行分割内容
        lines = content.split('\n')
        translated_lines = []
        
        # 设置源语言和目标语言
        src_lang = req.src_lang.split("_")[0]
        tgt_lang = req.tgt_lang.split("_")[0]
        tokenizer.src_lang = src_lang
        
        # 批量翻译
        for line in lines:
            line = line.strip()
            if not line:  # 跳过空行
                translated_lines.append("")
                continue
                
            # 编码输入文本
            encoded = tokenizer(line, return_tensors="pt", max_length=512, truncation=True)
            
            # 如果有GPU，将输入移至GPU
            if torch.cuda.is_available():
                encoded = {k: v.to("cuda") for k, v in encoded.items()}
            
            # 生成翻译
            generated_tokens = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.get_lang_id(tgt_lang),
                max_length=512,
                num_beams=5,
                early_stopping=True
            )
            
            # 解码翻译结果
            translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            translated_lines.append(translation)
            
        # 合并翻译结果
        translated_content = '\n'.join(translated_lines)
        
        # 生成下载文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        result_file_name = f"translated_{timestamp}.txt"
        result_file_path = os.path.join(download_dir, result_file_name)
        
        with open(result_file_path, "w", encoding="utf-8") as f:
            f.write(translated_content)
            
        return {
            "success": True,
            "translated_lines": len(translated_lines),
            "download_file": result_file_name
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    """下载翻译结果文件"""
    file_path = os.path.join(download_dir, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path=file_path, filename=file_name, media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 