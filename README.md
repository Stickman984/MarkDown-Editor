# Markdown 编辑器 (Qt版)

一个基于 PyQt6 的现代化 Markdown 编辑器，支持实时预览、多标签页、目录导航和丰富的快捷键操作。

## 主要特性

### 智能链接处理

- **Markdown 文件** (`.md`)：自动在新标签页中打开。
- **文本文件** (`.txt`, `.py`, `.json` 等)：使用自己设置的文本浏览器打开。
- **文件夹**：自动打开 Windows 资源管理器。
- **网页链接**：自动调用默认浏览器打开。

### 表格支持

- **表格助手**：方便在该程序中创建，修改表格


## 🛠️ 安装与运行

### 依赖安装
确保已安装 Python 3.x，然后安装所需库：
```bash
pip install PyQt6 PyQt6-WebEngine markdown
```

### 运行
```bash
python md_editor_qt.py
```

## 📝 使用说明

1. **启动**：程序启动后为空白窗口，您可以点击工具栏的"新建"或"打开"开始工作。
2. **目录**：点击工具栏最右侧的 "📑 目录" 按钮，可在右侧显示/隐藏文档大纲。
3. **视图控制**：在"视图"菜单或工具栏中，可以单独隐藏编辑器或预览窗口。

## 📦 打包建议
如果需要打包成 `.exe` 文件，建议使用 PyInstaller：
```bash
pyinstaller --noconsole --onefile --name="Tutu" md_editor_qt.py
pyinstaller --noconsole --icon="./pic/logo-open_eyes.png" --add-data "./pic;pic" --name="Tutu" md_editor_qt.py
```
