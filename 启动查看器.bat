@echo off
REM Markdown 文档查看器启动脚本
REM 使用指定的Python路径运行应用程序

set PYTHON_PATH=D:\Data_Rufei\Python312\python.exe
set SCRIPT_DIR=%~dp0

REM 如果有命令行参数（拖放的文件），传递给应用
if "%~1"=="" (
    "%PYTHON_PATH%" "%SCRIPT_DIR%md_viewer.py"
) else (
    "%PYTHON_PATH%" "%SCRIPT_DIR%md_viewer.py" "%~1"
)
