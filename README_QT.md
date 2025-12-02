# Qt版本 Markdown查看器说明

## 文件
- `md_viewer_qt.py` - Qt版本的主程序
- `requirements_qt.txt` - Qt版本所需依赖

## 安装依赖

```bash
pip install -r requirements_qt.txt
```

或者手动安装：
```bash
pip install PyQt6 PyQt6-WebEngine markdown
```

## 运行

```bash
python md_viewer_qt.py
```

或者打开特定文件：
```bash
python md_viewer_qt.py README.md
```

## Qt版本的优势

### 与tkinter版本对比

| 特性 | tkinter版本 | Qt版本 |
|------|-------------|--------|
| 缩放方式 | 重新计算CSS + 重新加载HTML | JavaScript动态修改CSS zoom |
| 缩放效果 | 有闪烁和跳动 | **完全无闪烁** |
| 滚动位置 | 需要手动保存和恢复 | **自动保持** |
| 渲染引擎 | tkhtml (较老) | **Chromium (现代)** |
| CSS支持 | 有限 | **完整** |
| 性能 | 一般 | **更好** |

### 核心改进

1. **无闪烁缩放**: 使用JavaScript直接修改CSS zoom属性，无需重新加载HTML
   ```python
   # 关键代码
   js_code = f"document.body.style.zoom = {zoom_level};"
   web_view.page().runJavaScript(js_code)
   ```

2. **完美的滚动位置保持**: 因为不重新加载HTML，滚动位置自然保持不变

3. **更好的链接拦截**: 通过`acceptNavigationRequest`方法优雅地处理链接点击

4. **现代化UI**: Qt的界面比tkinter更美观

## 功能清单

- ✅ 多标签页支持
- ✅ Markdown渲染
- ✅ 代码高亮
- ✅ 表格支持
- ✅ **无闪烁缩放** (关键改进)
- ✅ 链接处理 (本地文件、Markdown文件、外部URL)
- ✅ 快捷键支持
- ✅ 工具栏和菜单
- ✅ 刷新功能

## 使用建议

Qt版本提供了更好的用户体验，特别是在缩放功能上。如果您经常需要调整文档大小，强烈建议使用Qt版本。

tkinter版本可以作为备份，在不方便安装PyQt6的环境中使用。

## 打包成exe

### 安装PyInstaller

```bash
pip install pyinstaller
```

### 打包命令

**方法1：简单打包（单个exe，启动较慢）**
```bash
pyinstaller --onefile --windowed --name "MD-Viewer-Qt" md_viewer_qt.py
```

**方法2：文件夹打包（推荐，启动快）**
```bash
pyinstaller --windowed --name "MD-Viewer-Qt" md_viewer_qt.py
```

### 完整打包命令（推荐）

包含图标和优化选项：

```bash
pyinstaller --windowed ^
    --name "MD-Viewer-Qt" ^
    --add-data "README.md;." ^
    --hidden-import markdown.extensions.extra ^
    --hidden-import markdown.extensions.codehilite ^
    --hidden-import markdown.extensions.toc ^
    --hidden-import markdown.extensions.fenced_code ^
    --hidden-import markdown.extensions.tables ^
    --hidden-import markdown.extensions.nl2br ^
    md_viewer_qt.py
```

> **注意**：Windows下使用 `^` 作为续行符，Linux/Mac使用 `\`

### 打包后的文件位置

- **单文件模式**：`dist/MD-Viewer-Qt.exe`
- **文件夹模式**：`dist/MD-Viewer-Qt/MD-Viewer-Qt.exe`

### 运行打包后的程序

```bash
# 直接运行
dist\MD-Viewer-Qt.exe

# 打开特定文件
dist\MD-Viewer-Qt.exe README.md
```

### 打包注意事项

1. **首次打包较慢**：PyQt6和WebEngine较大，首次打包需要几分钟
2. **文件较大**：打包后的exe约100-150MB（包含Chromium引擎）
3. **杀毒软件**：部分杀毒软件可能误报，需要添加信任
4. **清理缓存**：如需重新打包，先删除 `build` 和 `dist` 文件夹

### 优化建议

如果exe太大，可以考虑：
- 使用文件夹模式而不是单文件模式
- 不打包markdown扩展（如果不需要某些功能）
- 使用UPX压缩（但可能增加启动时间）

