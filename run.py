import uvicorn
import sys

if __name__ == "__main__":
    print("启动多语言翻译服务...")
    print("正在加载本地模型，请稍等...")
    try:
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        confirm = input("\n检测到 Ctrl+C，确定要退出服务吗？(y/n): ")
        if confirm.lower() == 'y':
            print("服务已退出。")
            sys.exit(0)
        else:
            print("继续运行服务...")
            # 重新启动服务
            uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True) 