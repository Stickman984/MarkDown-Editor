#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown编辑器 - Qt版本（多标签页）
支持实时预览、语法高亮和多标签页管理的Markdown编辑器
"""

import os
import sys
import re
import subprocess
import webbrowser
import urllib.parse
import shutil
import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QSplitter, QPlainTextEdit,
    QFileDialog, QMessageBox, QToolBar, QStatusBar, QWidget, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLabel, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt, QTimer, pyqtSlot
from PyQt6.QtGui import (
    QAction, QKeySequence, QSyntaxHighlighter, QTextCharFormat,
    QColor, QFont, QTextCursor, QTextBlock, QIcon, QPixmap, QImage
)
import markdown


def resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 如果不是打包后的exe，使用脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)



class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown语法高亮器"""
    # ... (保持不变) ...
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 定义各种格式
        self.formats = {}
        
        # 标题格式 (# ## ###)
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#2c3e50"))
        header_format.setFontWeight(QFont.Weight.Bold)
        self.formats['header'] = header_format
        
        # 加粗格式 (**text** 或 __text__)
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#e74c3c"))
        bold_format.setFontWeight(QFont.Weight.Bold)
        self.formats['bold'] = bold_format
        
        # 斜体格式 (*text* 或 _text_)
        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#8e44ad"))
        italic_format.setFontItalic(True)
        self.formats['italic'] = italic_format
        
        # 代码格式 (`code`)
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#27ae60"))
        code_format.setFontFamily("Consolas")
        self.formats['code'] = code_format
        
        # 代码块格式 (```code```)
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(QColor("#16a085"))
        code_block_format.setFontFamily("Consolas")
        code_block_format.setBackground(QColor("#ecf0f1"))
        self.formats['code_block'] = code_block_format
        
        # 链接格式 [text](url)
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#3498db"))
        link_format.setFontUnderline(True)
        self.formats['link'] = link_format
        
        # 列表格式 (- * +)
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#f39c12"))
        self.formats['list'] = list_format
        
        # 引用格式 (>)
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#95a5a6"))
        quote_format.setFontItalic(True)
        self.formats['quote'] = quote_format
        
        # 定义正则表达式规则
        self.rules = [
            (r'^#{1,6}\s+.*$', self.formats['header']),
            (r'\*\*[^\*]+\*\*', self.formats['bold']),
            (r'__[^_]+__', self.formats['bold']),
            (r'\*[^\*]+\*', self.formats['italic']),
            (r'_[^_]+_', self.formats['italic']),
            (r'`[^`]+`', self.formats['code']),
            (r'\[([^\]]+)\]\([^\)]+\)', self.formats['link']),
            (r'^\s*[-\*\+]\s+', self.formats['list']),
            (r'^>\s+.*$', self.formats['quote']),
        ]
    
    def highlightBlock(self, text):
        """高亮当前块"""
        for pattern, format_obj in self.rules:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, format_obj)
        
        self.highlight_code_blocks(text)
    
    def highlight_code_blocks(self, text):
        """高亮代码块 ```code```"""
        prev_state = self.previousBlockState()
        in_code_block = prev_state == 1
        
        if text.strip().startswith('```'):
            in_code_block = not in_code_block
            self.setCurrentBlockState(1 if in_code_block else 0)
            self.setFormat(0, len(text), self.formats['code_block'])
        elif in_code_block:
            self.setCurrentBlockState(1)
            self.setFormat(0, len(text), self.formats['code_block'])
        else:
            self.setCurrentBlockState(0)


class MarkdownWebView(QWebEngineView):
    # ... (保持不变) ...
    def __init__(self, editor_tab, parent=None):
        super().__init__(parent)
        self.editor_tab = editor_tab
        self.zoom_level = 1.0
        
        # 创建自定义页面以拦截链接
        self.page_obj = MarkdownWebPage(self)
        self.setPage(self.page_obj)
        
        # 启用设置
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    
    def set_zoom(self, zoom_level):
        """设置缩放级别"""
        self.zoom_level = zoom_level
        js_code = f"document.body.style.zoom = {zoom_level};"
        self.page().runJavaScript(js_code)


class MarkdownWebPage(QWebEnginePage):
    # ... (保持不变) ...
    def __init__(self, web_view):
        super().__init__(web_view)
        self.web_view = web_view
    
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        """拦截导航请求"""
        # 只处理用户点击的链接
        if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            # 阻止默认导航，交给主窗口处理
            self.web_view.editor_tab.main_window.handle_link_click(url.toString())
            return False
        
        # 允许其他类型的导航（如初始加载）
        return True



class MarkdownTextEdit(QPlainTextEdit):
    """支持图片和文件粘贴的文本编辑器"""
    
    def __init__(self, editor_tab, parent=None):
        super().__init__(parent)
        self.editor_tab = editor_tab
        
    def canInsertFromMimeData(self, source):
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)
        
    def insertFromMimeData(self, source):
        # 确定基准目录
        if self.editor_tab.current_file:
            base_dir = os.path.dirname(self.editor_tab.current_file)
        else:
            # 如果是新文件，未保存，暂时使用当前工作目录
            base_dir = os.getcwd()
            
        # 1. 处理图片
        if source.hasImage():
            image = source.imageData()
            if image:
                # 创建图片目录
                pic_dir = os.path.join(base_dir, "pic")
                if not os.path.exists(pic_dir):
                    os.makedirs(pic_dir)
                    
                # 生成文件名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"image_{timestamp}.png"
                full_path = os.path.join(pic_dir, filename)
                
                # 保存图片
                # 注意：imageData()返回的是QVariant，PyQt6通常会自动解包为QImage/QPixmap
                # 如果是QPixmap需要转为QImage，但QMimeData通常存储QImage
                if hasattr(image, 'save'):
                    image.save(full_path, "PNG")
                else:
                    # 尝试转换
                    from PyQt6.QtGui import QImage
                    if isinstance(image, QImage):
                        image.save(full_path, "PNG")
                
                # 插入Markdown
                cursor = self.textCursor()
                cursor.insertText(f"![](./pic/{filename})")
                return
                
        # 2. 处理文件
        if source.hasUrls():
            has_handled_urls = False
            for url in source.urls():
                if url.isLocalFile():
                    src_path = url.toLocalFile()
                    if os.path.exists(src_path):
                        # 判断是否为图片文件（通过扩展名）
                        ext = os.path.splitext(src_path)[1].lower()
                        is_image_file = ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp']
                        
                        if is_image_file:
                            # 即使是文件复制，如果是图片，也放入 pic 目录
                            target_dir = os.path.join(base_dir, "pic")
                            if not os.path.exists(target_dir):
                                os.makedirs(target_dir)
                                
                            filename = os.path.basename(src_path)
                            # 处理文件名冲突
                            target_path = os.path.join(target_dir, filename)
                            if os.path.exists(target_path):
                                name, ext = os.path.splitext(filename)
                                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"{name}_{timestamp}{ext}"
                                target_path = os.path.join(target_dir, filename)
                                
                            shutil.copy2(src_path, target_path)
                            
                            cursor = self.textCursor()
                            cursor.insertText(f"![](./pic/{filename})")
                            has_handled_urls = True
                            
                        else:
                            # 其他文件放入 files 目录
                            target_dir = os.path.join(base_dir, "files")
                            if not os.path.exists(target_dir):
                                os.makedirs(target_dir)
                                
                            filename = os.path.basename(src_path)
                            # 处理文件名冲突
                            target_path = os.path.join(target_dir, filename)
                            if os.path.exists(target_path):
                                name, ext = os.path.splitext(filename)
                                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"{name}_{timestamp}{ext}"
                                target_path = os.path.join(target_dir, filename)
                                
                            try:
                                if os.path.isdir(src_path):
                                    shutil.copytree(src_path, target_path)
                                else:
                                    shutil.copy2(src_path, target_path)
                                    
                                cursor = self.textCursor()
                                cursor.insertText(f"[{filename}](./files/{filename})")
                                has_handled_urls = True
                            except Exception as e:
                                print(f"Copy failed: {e}")
            
            if has_handled_urls:
                return

        super().insertFromMimeData(source)


class EditorTab(QWidget):
    """单个编辑器标签页，包含编辑器和预览"""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.current_file = None
        self.is_modified = False
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 创建编辑器
        self.editor = MarkdownTextEdit(self)
        self.editor.setPlaceholderText("在此输入Markdown内容...")
        
        # 设置编辑器字体
        font = QFont("Consolas", 14)
        self.editor.setFont(font)
        
        # 应用语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 监听文本变化
        self.editor.textChanged.connect(self.on_text_changed)
        
        # 创建预览
        self.preview = MarkdownWebView(self)
        
        # 创建目录树
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("目录")
        self.toc_tree.header().setVisible(True)
        self.toc_tree.itemClicked.connect(self.on_toc_item_clicked)
        self.toc_tree.setVisible(False) # 默认隐藏
        
        # 添加到分割器
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.addWidget(self.toc_tree)
        
        # 设置初始比例 (45:45:10)
        self.splitter.setSizes([500, 500, 200])
        
        # 添加到布局
        layout.addWidget(self.splitter)
        
        # 创建预览更新定时器
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        
        # 同步滚动设置
        self.sync_scroll_enabled = True
        self.is_syncing = False  # 防止循环触发
        
        # 缩放设置
        self.editor_zoom_level = 1.0
        self.base_font_size = 14
        
        # 增量更新设置
        self.preview_initialized = False  # 预览页面是否已初始化
        self.last_base_url = None  # 上次的baseUrl，用于检测是否需要完全重新加载
        
        # 监听编辑器滚动
        self.editor.verticalScrollBar().valueChanged.connect(self.on_editor_scroll)
        
        # 监听预览窗口标题变化（用于接收滚动数据）
        # 注意：必须只连接一次，否则会导致重复触发滚动同步
        self.preview.page().titleChanged.connect(self.on_preview_title_changed)
        
        # 安装事件过滤器以捕获Ctrl+滚轮缩放
        self.editor.installEventFilter(self)
        self.editor.viewport().installEventFilter(self)  # 关键：也要监听viewport
        self.preview.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理Ctrl+滚轮缩放和Tab键"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QWheelEvent
        
        # 处理Tab键：智能补齐到4空格边界
        if event.type() == QEvent.Type.KeyPress and obj == self.editor:
            if event.key() == Qt.Key.Key_Tab:
                cursor = self.editor.textCursor()
                # 获取当前行光标位置（从行首开始算）
                pos_in_line = cursor.positionInBlock()
                # 计算需要补齐的空格数（到下一个4的倍数）
                spaces_needed = 4 - (pos_in_line % 4)
                cursor.insertText(" " * spaces_needed)
                return True
            elif event.key() == Qt.Key.Key_Backtab:  # Shift+Tab
                cursor = self.editor.textCursor()
                # 移动到行首
                cursor.movePosition(cursor.MoveOperation.StartOfLine)
                # 获取当前行文本
                block_text = cursor.block().text()
                # 计算行首有多少空格
                leading_spaces = len(block_text) - len(block_text.lstrip(' '))
                # 最多移除4个空格
                spaces_to_remove = min(leading_spaces, 4)
                if spaces_to_remove > 0:
                    cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, spaces_to_remove)
                    cursor.removeSelectedText()
                return True
        
        if event.type() == QEvent.Type.Wheel and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            wheel_event = event
            delta = wheel_event.angleDelta().y()
            
            if obj == self.editor or obj == self.editor.viewport():
                # 缩放编辑器
                if delta > 0:
                    self.editor_zoom_level = min(self.editor_zoom_level + 0.1, 3.0)
                else:
                    self.editor_zoom_level = max(self.editor_zoom_level - 0.1, 0.5)
                self.update_editor_zoom()
                return True
            elif obj == self.preview:
                # 缩放预览
                if delta > 0:
                    self.preview.zoom_level = min(self.preview.zoom_level + 0.1, 3.0)
                else:
                    self.preview.zoom_level = max(self.preview.zoom_level - 0.1, 0.2)
                self.preview.set_zoom(self.preview.zoom_level)
                return True
        
        return super().eventFilter(obj, event)
    
    def update_editor_zoom(self):
        """更新编辑器缩放"""
        new_font_size = int(self.base_font_size * self.editor_zoom_level)
        font = self.editor.font()
        font.setPointSize(new_font_size)
        self.editor.setFont(font)
    
    def on_editor_scroll(self):
        """编辑器滚动时同步预览"""
        if not self.sync_scroll_enabled or self.is_syncing:
            return
        
        self.is_syncing = True
        
        # 获取编辑器滚动位置（0.0-1.0）
        scrollbar = self.editor.verticalScrollBar()
        if scrollbar.maximum() > 0:
            scroll_ratio = scrollbar.value() / scrollbar.maximum()
        else:
            scroll_ratio = 0.0
        
        # 同步预览窗口滚动
        js_code = f"""
            var scrollRatio = {scroll_ratio};
            var scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            window.scrollTo(0, scrollHeight * scrollRatio);
        """
        self.preview.page().runJavaScript(js_code)
        
        QTimer.singleShot(100, lambda: setattr(self, 'is_syncing', False))
    
    def on_preview_scroll(self, scroll_y):
        """预览窗口滚动时同步编辑器"""
        if not self.sync_scroll_enabled or self.is_syncing:
            return
        
        self.is_syncing = True
        
        # scroll_y 是一个包含 [scrollY, scrollHeight, clientHeight] 的列表
        if len(scroll_y) >= 3:
            scroll_pos = scroll_y[0]
            scroll_height = scroll_y[1]
            client_height = scroll_y[2]
            
            max_scroll = scroll_height - client_height
            if max_scroll > 0:
                scroll_ratio = scroll_pos / max_scroll
            else:
                scroll_ratio = 0.0
            
            # 同步编辑器滚动
            scrollbar = self.editor.verticalScrollBar()
            if scrollbar.maximum() > 0:
                target_value = int(scrollbar.maximum() * scroll_ratio)
                scrollbar.setValue(target_value)
        
        QTimer.singleShot(100, lambda: setattr(self, 'is_syncing', False))
    
    def on_text_changed(self):
        """文本改变时触发"""
        self.is_modified = True
        self.main_window.update_tab_title(self)
        
        # 使用定时器防抖，300ms后更新预览
        self.preview_timer.stop()
        self.preview_timer.start(300)
    
    def update_toc(self):
        """更新目录"""
        self.toc_tree.clear()
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        # 栈用于跟踪父节点：[(level, item)]
        stack = [] 
        
        for i, line in enumerate(lines):
            # 匹配标题行 (# H1, ## H2 等)
            match = re.match(r'^(#{1,6})\s+(.*)', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                
                item = QTreeWidgetItem([title])
                item.setData(0, Qt.ItemDataRole.UserRole, i) # 存储行号
                
                # 找到正确的父节点
                while stack and stack[-1][0] >= level:
                    stack.pop()
                
                if stack:
                    parent_item = stack[-1][1]
                    parent_item.addChild(item)
                else:
                    self.toc_tree.addTopLevelItem(item)
                
                stack.append((level, item))
        
        self.toc_tree.expandAll()

    def on_toc_item_clicked(self, item, column):
        """点击目录项跳转"""
        line_number = item.data(0, Qt.ItemDataRole.UserRole)
        if line_number is not None:
            # 移动光标到对应行
            cursor = self.editor.textCursor()
            block = self.editor.document().findBlockByLineNumber(line_number)
            cursor.setPosition(block.position())
            self.editor.setTextCursor(cursor)
            self.editor.centerCursor() # 滚动到可见区域
            self.editor.setFocus()

    def update_preview(self):
        """更新预览（支持增量DOM更新以减少闪烁）"""
        # 更新目录
        self.update_toc()
        
        # 锁定同步滚动，防止预览更新时干扰编辑器
        self.is_syncing = True
        
        # 保存编辑器当前状态（绝对值，而非比例）
        editor_scroll_value = self.editor.verticalScrollBar().value()
        cursor_position = self.editor.textCursor().position()

        # 计算预览滚动比例（用于恢复预览位置）
        preview_scroll_ratio = 0.0
        scrollbar = self.editor.verticalScrollBar()
        if scrollbar.maximum() > 0:
            preview_scroll_ratio = scrollbar.value() / scrollbar.maximum()
        
        # 获取编辑器内容
        text = self.editor.toPlainText()
        
        # 预处理：修复特殊格式显示问题
        text = self.main_window.preprocess_markdown(text)
        
        # 转换为HTML
        self.main_window.md.reset()
        html_content = self.main_window.md.convert(text)
        
        # 获取baseUrl用于相对路径解析
        base_url = None
        base_url_str = ""
        if self.current_file:
            base_dir = os.path.dirname(self.current_file)
            base_url = QUrl.fromLocalFile(base_dir + "/")
            base_url_str = base_dir
        
        # 检查是否需要完全重新加载（首次加载或baseUrl变化）
        need_full_reload = not self.preview_initialized or self.last_base_url != base_url_str
        
        if need_full_reload:
            # 完全重新加载：使用setHtml
            self._full_reload_preview(html_content, base_url, base_url_str, preview_scroll_ratio)
        else:
            # 增量更新：使用JavaScript更新内容
            self._incremental_update_preview(html_content)
        
        # 恢复编辑器滚动位置和光标位置（确保编辑器不跳动）
        self.editor.verticalScrollBar().setValue(editor_scroll_value)
        cursor = self.editor.textCursor()
        cursor.setPosition(cursor_position)
        self.editor.setTextCursor(cursor)
        
        # 延迟解锁同步，等待预览加载完成
        delay = 500 if need_full_reload else 50
        QTimer.singleShot(delay, lambda: setattr(self, 'is_syncing', False))
    
    def _full_reload_preview(self, html_content, base_url, base_url_str, preview_scroll_ratio):
        """完全重新加载预览页面"""
        # 包装样式，但内容放在特定容器中
        styled_html = self.main_window.wrap_html(
            f'<div id="md-content">{html_content}</div>',
            self.preview.zoom_level,
            base_path=os.path.dirname(self.current_file) if self.current_file else None
        )
        
        # 添加滚动监听脚本和自动恢复滚动位置脚本
        scroll_script = f"""
        <script>
        let scrollTimeout;
        let isInitialLoad = true;
        
        window.addEventListener('scroll', function() {{
            // 忽略初始加载时的滚动事件
            if (isInitialLoad) return;
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(function() {{
                // 发送滚动信息到Qt
                const scrollData = [
                    window.scrollY,
                    document.documentElement.scrollHeight,
                    window.innerHeight
                ];
                // 注意：这里我们通过修改title来传递数据（一个技巧）
                document.title = 'SCROLL:' + JSON.stringify(scrollData);
            }}, 50);
        }});
        
        // 页面加载后恢复滚动位置
        window.addEventListener('load', function() {{
            var scrollRatio = {preview_scroll_ratio};
            var scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            window.scrollTo(0, scrollHeight * scrollRatio);
            
            // 延迟后开始监听用户滚动
            setTimeout(function() {{
                isInitialLoad = false;
            }}, 100);
        }});
        </script>
        """
        styled_html = styled_html.replace('</body>', scroll_script + '</body>')
        
        # 更新预览，提供baseUrl
        if base_url:
            self.preview.setHtml(styled_html, base_url)
        else:
            self.preview.setHtml(styled_html)
        
        # 标记为已初始化
        self.preview_initialized = True
        self.last_base_url = base_url_str
    
    def _incremental_update_preview(self, html_content):
        """增量更新预览内容（不重新加载整个页面）"""
        import json
        # 转义HTML内容用于JavaScript
        escaped_content = json.dumps(html_content)
        
        # 使用JavaScript更新内容容器
        js_code = f"""
        (function() {{
            var container = document.getElementById('md-content');
            if (container) {{
                container.innerHTML = {escaped_content};
            }}
        }})();
        """
        self.preview.page().runJavaScript(js_code)

    def on_preview_title_changed(self, title):
        """预览窗口标题改变时（用于接收滚动数据）"""
        if title.startswith('SCROLL:'):
            try:
                import json
                scroll_data = json.loads(title[7:])
                self.on_preview_scroll(scroll_data)
            except:
                pass
    
    def load_file(self, filename, anchor=None):
        """加载文件到此标签页"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.editor.setPlainText(content)
            self.current_file = filename
            self.is_modified = False
            self.preview_initialized = False  # 重置，确保新文件触发完全重新加载
            self.main_window.update_tab_title(self)
            self.main_window.statusbar.showMessage(f"已打开: {filename}")
            self.update_toc() # 加载文件后更新目录
            
            if anchor:
                # 使用定时器确保内容加载完成后再滚动
                QTimer.singleShot(100, lambda: self.scroll_to_anchor(anchor))
                
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"无法打开文件:\n{str(e)}")
            
    def scroll_to_anchor(self, anchor):
        """滚动到指定锚点"""
        if not anchor:
            return
            
        # 简单匹配：寻找包含锚点文本的标题行
        # 锚点通常是URL编码的，这里已经解码
        # 实际标题可能包含空格、大小写差异
        
        target_text = anchor.lower().replace('-', ' ').replace('_', ' ')
        
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#'):
                # 提取标题文本
                header_text = line.lstrip('#').strip().lower()
                
                # 尝试匹配
                # 1. 直接包含
                # 2. 移除空格后包含
                if target_text in header_text or \
                   target_text.replace(' ', '') in header_text.replace(' ', ''):
                    
                    # 找到匹配行，滚动到该行
                    cursor = self.editor.textCursor()
                    block = self.editor.document().findBlockByLineNumber(i)
                    cursor.setPosition(block.position())
                    self.editor.setTextCursor(cursor)
                    self.editor.centerCursor()
                    self.editor.setFocus()
                    return
    
    def save_file(self):
        """保存文件"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """另存为"""
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "保存Markdown文件",
            "",
            "Markdown文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filename:
            self.save_to_file(filename)
    
    def save_to_file(self, filename):
        """保存到指定文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            
            self.current_file = filename
            self.is_modified = False
            self.main_window.update_tab_title(self)
            self.main_window.statusbar.showMessage(f"已保存: {filename}")
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"无法保存文件:\n{str(e)}")


class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown 编辑器 (Qt)")
        self.resize(1200, 800)
        self.center_window()
        
        # Notepad++路径
        self.notepadpp_path = r"C:\Program Files\Notepad++\notepad++.exe"
        
        # Markdown转换器
        # nl2br: 将单个换行符转换为<br>，支持列表中的换行显示
        # sane_lists: 更合理的列表解析
        self.md = markdown.Markdown(extensions=[
            'extra',           # 包含多个扩展：abbr, attr_list, def_list, fenced_code, footnotes, tables
            'codehilite',      # 代码高亮
            'toc',             # 目录
            'fenced_code',     # 围栏代码块（已包含在extra中，但明确声明）
            'tables',          # 表格（已包含在extra中，但明确声明）
            'sane_lists',      # 更合理的列表解析
            'nl2br',           # 换行符转<br>（支持列表中的换行）
        ])


        
        
        # 创建UI
        # self.create_menu() # Removed
        self.create_toolbar()
        self.create_statusbar()
        self.create_tab_widget()
        
        # 检查 pygments 是否安装（用于代码高亮）
        try:
            import pygments
            self.has_pygments = True
        except ImportError:
            self.has_pygments = False
            QTimer.singleShot(1000, lambda: self.statusbar.showMessage("警告: 未检测到 pygments 库，代码高亮可能无法正常工作。请运行 'pip install pygments'", 10000))
        
        # 启用拖放支持
        self.setAcceptDrops(True)
        
        # 不自动创建标签页，用户可以手动打开文件或新建
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖放完成事件"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if os.path.exists(file_path):
                # 检查是否是文件夹
                if os.path.isdir(file_path):
                    # 如果是文件夹，可以选择打开文件夹内的所有md文件，或者忽略
                    # 这里简单处理：只处理文件
                    pass
                else:
                    self.open_file_in_tab(file_path, in_new_tab=True)
    

    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("Main")
        # 设置工具栏样式：选中状态背景显示淡黄色
        toolbar.setStyleSheet("""
            QToolButton:checked {
                background-color: #f8f1ef; /* 淡黄色 */
                border: 1px solid #F0E68C;
                border-radius: 3px;
            }
        """)
        self.addToolBar(toolbar)
        
        # 1. New Tab
        new_tab_action = QAction("📑 新标签页", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(self.new_tab)
        toolbar.addAction(new_tab_action)
        self.addAction(new_tab_action)  # Add to window for global shortcut
        
        # 2. Open
        open_action = QAction("📂 打开", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        self.addAction(open_action)  # Add to window for global shortcut
        
        # 3. Save
        save_action = QAction("💾 保存", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        self.addAction(save_action)  # Add to window for global shortcut
        
        # 3.5 Close Tab (Hidden Action for shortcut)
        close_tab_action = QAction("关闭标签页", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self.close_current_tab)
        self.addAction(close_tab_action)  # Add to window for global shortcut
        
        toolbar.addSeparator()
        
        # 4. Set Color
        color_action = QAction("🎨 颜色", self)
        color_action.triggered.connect(self.insert_color_tag)
        toolbar.addAction(color_action)
        
        # 5. Table Helper
        table_action = QAction("📊 表格助手", self)
        table_action.triggered.connect(self.open_table_helper)
        toolbar.addAction(table_action)

        # Spacer to push View controls to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # 6. View Controls (Right Aligned)
        
        # Editor Toggle
        self.toggle_editor_action = QAction("📝 编辑器", self)
        self.toggle_editor_action.setCheckable(True)
        self.toggle_editor_action.setChecked(True)
        self.toggle_editor_action.triggered.connect(self.toggle_editor)
        toolbar.addAction(self.toggle_editor_action)
        
        # Preview Toggle
        self.toggle_preview_action = QAction("🖼 预览", self)
        self.toggle_preview_action.setCheckable(True)
        self.toggle_preview_action.setChecked(True)
        self.toggle_preview_action.triggered.connect(self.toggle_preview)
        toolbar.addAction(self.toggle_preview_action)
        
        # TOC Toggle
        self.toggle_toc_toolbar_action = QAction("📑 目录", self)
        self.toggle_toc_toolbar_action.setCheckable(True)
        self.toggle_toc_toolbar_action.setChecked(False) # Default hidden? Or Check initial state
        self.toggle_toc_toolbar_action.triggered.connect(self.toggle_toc)
        toolbar.addAction(self.toggle_toc_toolbar_action)


    
    def create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
    
    def create_tab_widget(self):
        """创建标签页容器"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.setCentralWidget(self.tab_widget)
        
        # 创建背景标签（用于无标签页时显示）
        # 注意：将其作为tab_widget的子控件，这样它只会显示在内容区域
        self.background_label = QLabel(self.tab_widget)
        self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.background_label.setScaledContents(False)  # 不拉伸内容
        
        # 尝试加载背景图片
        bg_path = resource_path("cat_background_1764666718697.png")
        if os.path.exists(bg_path):
            pixmap = QPixmap(bg_path)
            # 保持宽高比缩放图片
            self.background_pixmap = pixmap
            self.background_label.setPixmap(pixmap.scaled(
                800, 600, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.background_pixmap = None
            self.background_label.setText("没有打开的文件\n拖拽文件到此处打开")
            self.background_label.setStyleSheet("QLabel { color: #bdc3c7; font-size: 24px; font-weight: bold; }")
        
        self.background_label.hide()  # 默认隐藏
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        if hasattr(self, 'tab_widget') and hasattr(self, 'background_label'):
            # 调整背景标签大小为tab_widget的内容区域
            self.background_label.setGeometry(self.tab_widget.rect())
            
            # 如果有背景图片，重新缩放以适应窗口大小
            if hasattr(self, 'background_pixmap') and self.background_pixmap:
                size = self.tab_widget.size()
                scaled_pixmap = self.background_pixmap.scaled(
                    size.width(), size.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.background_label.setPixmap(scaled_pixmap)
            
            self.update_background_visibility()
            
    def update_background_visibility(self):
        """更新背景可见性"""
        if self.tab_widget.count() == 0:
            self.background_label.show()
            self.background_label.raise_()  # 确保在最上层（因为没有标签页时）
        else:
            self.background_label.hide()
    
    def new_tab(self):
        """创建新标签页"""
        tab = EditorTab(self)
        index = self.tab_widget.addTab(tab, "新文档 *")
        self.tab_widget.setCurrentIndex(index)
        tab.editor.setFocus()
        self.update_background_visibility()
        return tab
        
        # 设置欢迎内容
        welcome_text = """# 欢迎使用Markdown编辑器

## 功能特性

- **多标签页**：支持同时编辑多个文件
- **实时预览**：在左侧编辑，右侧实时看到效果
- **语法高亮**：不同的Markdown语法用不同颜色显示
- **分栏调节**：拖动中间分隔线调节编辑器和预览的大小

## 快速开始

1. 点击"打开"按钮打开现有的Markdown文件
2. 或者直接在左侧开始输入
3. 使用 `Ctrl+S` 保存文件
4. 使用 `Ctrl+T` 新建标签页

现在开始编辑吧！
"""
        tab.editor.setPlainText(welcome_text)
        tab.update_preview()
        
        # 添加到标签页容器
        index = self.tab_widget.addTab(tab, "新标签页")
        self.tab_widget.setCurrentIndex(index)
    
    def get_current_tab(self):
        """获取当前标签页"""
        return self.tab_widget.currentWidget()
    
    def update_tab_title(self, tab):
        """更新标签页标题"""
        index = self.tab_widget.indexOf(tab)
        if index >= 0:
            title = os.path.basename(tab.current_file) if tab.current_file else "新标签页"
            if tab.is_modified:
                title += " *"
            self.tab_widget.setTabText(index, title)
            
            # 更新窗口标题
            if tab == self.get_current_tab():
                window_title = "Markdown 编辑器 (Qt)"
                if tab.current_file:
                    window_title += f" - {os.path.basename(tab.current_file)}"
                if tab.is_modified:
                    window_title += " *"
                self.setWindowTitle(window_title)
    
    def on_tab_changed(self, index):
        """标签页切换事件"""
        tab = self.get_current_tab()
        if tab:
            self.update_tab_title(tab)
            if tab.current_file:
                self.statusbar.showMessage(f"当前: {tab.current_file}")
            else:
                self.statusbar.showMessage("就绪")
    
    def new_file(self):
        """新建文件（在当前标签页）"""
        tab = self.get_current_tab()
        if tab:
            if tab.is_modified:
                reply = QMessageBox.question(
                    self, "保存更改",
                    "当前文件已修改，是否保存？",
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Discard | 
                    QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Save:
                    tab.save_file()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return
            
            tab.editor.clear()
            tab.current_file = None
            tab.is_modified = False
            self.update_tab_title(tab)
    
    def open_file(self):
        """打开文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "打开Markdown文件",
            "",
            "Markdown文件 (*.md *.markdown *.mdown);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filename:
            # 总是在新标签页打开
            self.open_file_in_tab(filename, in_new_tab=True)
    
    def open_file_in_tab(self, filename, in_new_tab=False, anchor=None):
        """在标签页中打开文件"""
        if in_new_tab:
            self.new_tab()
        
        tab = self.get_current_tab()
        if tab:
            tab.load_file(filename, anchor)
    
    def save_file(self):
        """保存文件"""
        tab = self.get_current_tab()
        if tab:
            tab.save_file()
    
    def save_file_as(self):
        """另存为"""
        tab = self.get_current_tab()
        if tab:
            tab.save_file_as()
    
    def close_tab(self, index):
        """关闭指定标签页"""
        tab = self.tab_widget.widget(index)
        if tab and tab.is_modified:
            reply = QMessageBox.question(
                self, "保存更改",
                f"'{os.path.basename(tab.current_file) if tab.current_file else '新标签页'}' 已修改，是否保存？",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                tab.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # 允许关闭所有标签页
        self.tab_widget.removeTab(index)
        self.update_background_visibility()
    
    def close_current_tab(self):
        """关闭当前标签页"""
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)
    
    def toggle_editor(self):
        """切换编辑器显示/隐藏"""
        tab = self.get_current_tab()
        if tab:
            if tab.editor.isVisible():
                tab.editor.hide()
                self.toggle_editor_action.setChecked(False)
            else:
                tab.editor.show()
                self.toggle_editor_action.setChecked(True)
    
    def toggle_preview(self):
        """切换预览显示/隐藏"""
        tab = self.get_current_tab()
        if tab:
            if tab.preview.isVisible():
                tab.preview.hide()
                self.toggle_preview_action.setChecked(False)
            else:
                tab.preview.show()
                self.toggle_preview_action.setChecked(True)
    
    def toggle_toc(self):
        """切换目录显示/隐藏"""
        tab = self.get_current_tab()
        if tab:
            if tab.toc_tree.isVisible():
                tab.toc_tree.hide()
                self.toggle_toc_toolbar_action.setChecked(False)
            else:
                tab.toc_tree.show()
                self.toggle_toc_toolbar_action.setChecked(True)

    def open_table_helper(self):
        """打开表格助手"""
        try:
            from table_helper import TableHelperDialog
            
            # 获取当前选中的文本
            tab = self.get_current_tab()
            initial_content = None
            if tab:
                cursor = tab.editor.textCursor()
                if cursor.hasSelection():
                    initial_content = cursor.selectedText().replace("\u2029", "\n") # Qt text replacement for paragraph separator
            
            dialog = TableHelperDialog(self, initial_content)
            
            if dialog.exec():
                new_content = dialog.generate_content()
                
                # 插入/替换文本
                if tab:
                    cursor = tab.editor.textCursor()
                    cursor.beginEditBlock()
                    if cursor.hasSelection():
                        cursor.removeSelectedText()
                    cursor.insertText(new_content)
                    cursor.endEditBlock()
                    
        except ImportError:
            QMessageBox.warning(self, "错误", "无法加载表格助手模块(table_helper.py)")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"表格助手出错:\n{str(e)}")



    def insert_color_tag(self):
        """插入颜色标签"""
        tab = self.get_current_tab()
        if not tab:
            return
            
        from PyQt6.QtWidgets import QColorDialog
        
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "选择颜色")
        if color.isValid():
            tag_start = f'<font color="{color.name()}">'
            tag_end = '</font>'
            
            self._wrap_selection(tab.editor, tag_start, tag_end)
            
    def _wrap_selection(self, editor, start_tag, end_tag):
        """在选中文本前后插入标签"""
        cursor = editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"{start_tag}{text}{end_tag}")
        else:
            cursor.insertText(f"{start_tag}{end_tag}")
            # 移动光标到标签中间
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(end_tag))
            editor.setTextCursor(cursor)
            editor.setFocus()
    
    def handle_link_click(self, url):
        """处理链接点击事件"""
        try:
            # 分离锚点
            anchor = None
            if '#' in url:
                url, anchor = url.rsplit('#', 1)
                anchor = urllib.parse.unquote(anchor)
            
            # 解码URL
            decoded_url = urllib.parse.unquote(url)
            
            # 处理 file:// 前缀
            if decoded_url.startswith('file:///'):
                decoded_url = decoded_url[8:]
            elif decoded_url.startswith('file:'):
                decoded_url = decoded_url[5:]
            
            # Windows下路径处理
            if os.name == 'nt' and decoded_url.startswith('/') and len(decoded_url) > 2 and decoded_url[2] == ':':
                decoded_url = decoded_url[1:]
            
            # 规范化路径分隔符
            decoded_url = os.path.normpath(decoded_url)
            
            # 处理相对路径
            tab = self.get_current_tab()
            if not os.path.exists(decoded_url) and not os.path.isabs(decoded_url):
                if tab and tab.current_file:
                    base_dir = os.path.dirname(tab.current_file)
                    decoded_url = os.path.normpath(os.path.join(base_dir, decoded_url))
            
            # 检查是否是本地文件或文件夹
            if os.path.exists(decoded_url):
                if os.path.isdir(decoded_url):
                    # 文件夹 - 使用资源管理器打开
                    os.startfile(decoded_url)
                    self.statusbar.showMessage(f"已在资源管理器中打开: {decoded_url}")
                elif os.path.isfile(decoded_url):
                    # 文件 - 根据扩展名处理
                    ext = os.path.splitext(decoded_url)[1].lower()
                    
                    if ext in ['.md', '.markdown', '.mdown']:
                        # Markdown文件 - 在新标签页打开
                        self.open_file_in_tab(decoded_url, in_new_tab=True, anchor=anchor)
                    elif ext in ['.txt', '.log', '.json', '.xml', '.yaml', '.yml', 
                                '.py', '.js', '.java', '.c', '.cpp', '.h', '.cs',
                                '.html', '.css', '.php', '.rb', '.go', '.rs', '.sh',
                                '.bat', '.ini', '.cfg', '.conf']:
                        # 文本文件 - 使用Notepad++打开
                        if os.path.exists(self.notepadpp_path):
                            subprocess.Popen([self.notepadpp_path, decoded_url])
                            self.statusbar.showMessage(f"已在Notepad++中打开: {os.path.basename(decoded_url)}")
                        else:
                            os.startfile(decoded_url)
                            self.statusbar.showMessage(f"已打开: {os.path.basename(decoded_url)}")
                    else:
                        # 其他文件 - 使用系统默认程序
                        os.startfile(decoded_url)
                        self.statusbar.showMessage(f"已打开: {os.path.basename(decoded_url)}")
            else:
                # 不是本地文件，可能是URL - 使用默认浏览器打开
                webbrowser.open(url)
                self.statusbar.showMessage(f"已在浏览器中打开: {url}")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开链接:\n{str(e)}")
    
    def preprocess_markdown(self, text):
        """
        预处理Markdown文本
        
        解决问题：
        用户输入的 `[key]: [value]` 格式（常见于某些日志或配置）会被Markdown解析器
        误认为是"参考链接定义"(Reference Link Definition)而隐藏不显示。
        
        改进逻辑：
        1. 逐行处理
        2. 检测是否在代码块中（``` 或 4空格缩进）
        3. 只有在这个模式出现在普通文本中时才进行转义
        """
        lines = text.split('\n')
        processed_lines = []
        
        in_code_block = False
        
        # 匹配模式：[key]: [value]
        # 改进：不仅匹配行首，还匹配块引用(>)和列表项(-/+/*)前缀
        # 这样可以修复块引用中或列表中的内容显示问题
        # Group 1: Indent/Quotes (e.g. "  > > ")
        # Group 2: Bullet (optional)
        # Group 3: Space after bullet (optional)
        # Group 4: Key
        # Group 5: Space
        # Group 6: Value
        pattern = re.compile(r'^([\s>]*)(?:([-*+])(\s+))?\[([^\]\n]+)\]:(\s*)\[([^\]\n]+)\]')
        
        def replace_func(m):
            prefix = m.group(1)
            bullet = m.group(2) or ''
            bullet_space = m.group(3) or ''
            key = m.group(4)
            mid_space = m.group(5)
            val = m.group(6)
            # 转义第一个 [ 为 \[
            return f"{prefix}{bullet}{bullet_space}\\[{key}]:{mid_space}[{val}]"
        
        # 匹配引用块中的围栏代码块起始/结束
        # Group 1: Prefix (e.g. "> ")
        # Group 2: Fence (e.g. "```")
        bq_fence_pattern = re.compile(r'^(\s*(?:>\s*)+)(```|~~~)\s*$')
        in_bq_fence_block = False
        bq_prefix = ""
        
        # 匹配列表项中的围栏代码块（4+空格缩进）
        # Group 1: 缩进空格
        # Group 2: 围栏标记
        list_fence_pattern = re.compile(r'^(\s{4,})(```|~~~)\s*$')
        in_list_fence_block = False
        list_indent = ""
        
        for line in lines:
            # 1. 处理引用块中的围栏代码块
            # python-markdown不支持在引用块中使用围栏代码块（即使是fenced_code插件）
            # 必须将其转换为缩进代码块（即在引用标记后加4个空格）才能正确渲染为代码块
            
            if in_bq_fence_block:
                # 检查是否中断引用（即不再以相同前缀开头）
                if not line.startswith(bq_prefix):
                    in_bq_fence_block = False
                    # 继续后续处理（RegEx escape等）
                
                # 检查结束围栏
                elif line.strip() == (bq_prefix + "```").strip() or line.strip() == (bq_prefix + "~~~").strip():
                    # 结束围栏，丢弃该行
                    in_bq_fence_block = False
                    continue
                else:
                    # 内容行：转换为缩进代码块
                    # 保持引用前缀，但在内容前添加4个空格
                    content = line[len(bq_prefix):]
                    # 如果content本身有缩进，保留它
                    new_line = bq_prefix + "    " + content
                    processed_lines.append(new_line)
                    continue
            
            # 检查开始围栏（引用块）
            bq_match = bq_fence_pattern.match(line)
            if bq_match:
                in_bq_fence_block = True
                bq_prefix = bq_match.group(1)
                # 丢弃开始围栏行
                continue
            
            # 1.5 处理列表项中的围栏代码块
            # python-markdown对列表内的围栏代码块支持不佳，会渲染为inline code
            # 将其转换为缩进代码块（在原有缩进基础上再加4个空格）
            
            if in_list_fence_block:
                # 检查是否还在列表缩进内
                if line.strip() == "" or line.startswith(list_indent):
                    # 检查结束围栏
                    stripped_line = line.strip()
                    if stripped_line == "```" or stripped_line == "~~~":
                        # 结束围栏，丢弃该行，并插入空行以正确分隔后续列表项
                        in_list_fence_block = False
                        processed_lines.append("")  # 插入空行
                        continue
                    else:
                        # 内容行：转换为缩进代码块
                        # 保持原有缩进，再添加4个空格
                        if line.startswith(list_indent):
                            content = line[len(list_indent):]
                            new_line = list_indent + "    " + content
                            processed_lines.append(new_line)
                        else:
                            processed_lines.append(line)
                        continue
                else:
                    # 缩进中断，退出列表代码块模式
                    in_list_fence_block = False
            
            # 检查开始围栏（列表项）
            list_match = list_fence_pattern.match(line)
            if list_match:
                in_list_fence_block = True
                list_indent = list_match.group(1)
                # 插入一个缩进空行（python-markdown需要空行才能识别为代码块）
                processed_lines.append(list_indent)
                # 丢弃开始围栏行
                continue

            # 2. 检测并修复根级围栏代码块标记
            stripped = line.lstrip()
            indent_len = len(line) - len(stripped)
            
            # 自动修复：如果围栏代码块有少量缩进（1-3空格），这是无效Markdown，
            # python-markdown会将其作为文本处理，导致Reference Link丢失或需要丑陋的转义。
            # 我们将其强制"去缩进"，转变为合法的顶层代码块。
            if (stripped.startswith('```') or stripped.startswith('~~~')) and indent_len < 4 and not line.strip().startswith('>'):
                line = stripped # 去除缩进
                # 重新计算缩进（现在是0）
                indent_len = 0
            
            # 3. 检测代码块状态 (用于Regex保护)
            # 只有顶格的（无缩进）围栏才被视为代码块
            if line.startswith('```') or line.startswith('~~~'):
                in_code_block = not in_code_block
                processed_lines.append(line)
                continue
                
            # 如果在代码块内，直接保留
            if in_code_block:
                processed_lines.append(line)
                continue
            
            # 4. 检测缩进代码块（4个空格或1个Tab）
            indent_match = re.match(r'^(\s*)', line)
            current_indent_len = 0
            if indent_match:
                indent_str = indent_match.group(1)
                current_indent_len = len(indent_str.replace('\t', '    '))
            
            if current_indent_len >= 4:
                # 认为是缩进代码块，不处理
                processed_lines.append(line)
                continue
            
            # 5. 在普通文本中匹配特定模式并转义
            if pattern.match(line):
                line = pattern.sub(replace_func, line)
                
            processed_lines.append(line)
            
        return '\n'.join(processed_lines)

    def wrap_html(self, content, zoom_level=1.0, base_path=None):
        """包装HTML内容并添加样式"""
        
        # 如果有 base_path，生成 base 标签用于正确解析相对链接
        base_tag = ""
        if base_path:
            # 将 Windows 路径转换为 URL 格式
            base_url = base_path.replace('\\', '/')
            if not base_url.endswith('/'):
                base_url += '/'
            base_tag = f'<base href="file:///{base_url}">'
        
        css = f"""
        <style>
            body {{
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
                font-size: 18px;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 20px auto;
                padding: 20px;
                background-color: #fff;
                zoom: {zoom_level};
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
            }}
            h1 {{
                font-size: 2em;
                border-bottom: 2px solid #eaecef;
                padding-bottom: 0.3em;
            }}
            h2 {{
                font-size: 1.5em;
                border-bottom: 1px solid #eaecef;
                padding-bottom: 0.3em;
            }}
            h3 {{ font-size: 1.25em; }}
            h4 {{ font-size: 1em; }}
            code {{
                background-color: #f6f8fa;
                color: #24292e;
                padding: 0.2em 0.4em;
                margin: 0;
                font-size: 100%;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', 'Cascadia Code', monospace;
            }}
            pre {{
                background-color: #f6f8fa;
                padding: 16px;
                overflow-x: auto;
                overflow-y: hidden;
                font-size: 100%;
                line-height: 1.45;
                border-radius: 6px;
                border: 1px solid #d1d5da;
                white-space: pre;
                margin: 8px 0;
            }}
            pre code {{
                background-color: transparent;
                color: #24292e;
                padding: 0;
            }}
            blockquote {{
                padding: 0 1em;
                color: #6a737d;
                border-left: 0.25em solid #dfe2e5;
                margin: 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 16px 0;
            }}
            table th, table td {{
                padding: 6px 13px;
                border: 1px solid #dfe2e5;
            }}
            table th {{
                background-color: #f6f8fa;
                font-weight: 600;
            }}
            table tr:nth-child(even) {{
                background-color: #f6f8fa;
            }}
            a {{
                color: #0366d6;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
            ul, ol {{
                padding-left: 2em;
            }}
            li {{
                margin: 0.25em 0;
            }}
            li > p {{
                margin: 0.25em 0;
            }}
            li > pre {{
                white-space: pre;
                margin: 8px 0;
            }}
            hr {{
                height: 0.25em;
                padding: 0;
                margin: 24px 0;
                background-color: #e1e4e8;
                border: 0;
            }}
            
            /* Pygments Syntax Highlighting (GitHub style) */
            .codehilite .hll {{ background-color: #ffffcc }}
            .codehilite .c {{ color: #6a737d; font-style: italic }} /* Comment */
            .codehilite .err {{ color: #a61717; background-color: #e3d2d2 }} /* Error */
            .codehilite .k {{ color: #d73a49; font-weight: bold }} /* Keyword */
            .codehilite .o {{ color: #d73a49; font-weight: bold }} /* Operator */
            .codehilite .cm {{ color: #6a737d; font-style: italic }} /* Comment.Multiline */
            .codehilite .cp {{ color: #6a737d; font-weight: bold }} /* Comment.Preproc */
            .codehilite .c1 {{ color: #6a737d; font-style: italic }} /* Comment.Single */
            .codehilite .cs {{ color: #6a737d; font-weight: bold; font-style: italic }} /* Comment.Special */
            .codehilite .gd {{ color: #000000; background-color: #ffdddd }} /* Generic.Deleted */
            .codehilite .ge {{ font-style: italic }} /* Generic.Emph */
            .codehilite .gr {{ color: #aa0000 }} /* Generic.Error */
            .codehilite .gh {{ color: #999999 }} /* Generic.Heading */
            .codehilite .gi {{ color: #000000; background-color: #ddffdd }} /* Generic.Inserted */
            .codehilite .go {{ color: #888888 }} /* Generic.Output */
            .codehilite .gp {{ color: #555555 }} /* Generic.Prompt */
            .codehilite .gs {{ font-weight: bold }} /* Generic.Strong */
            .codehilite .gu {{ color: #aaaaaa }} /* Generic.Subheading */
            .codehilite .gt {{ color: #aa0000 }} /* Generic.Traceback */
            .codehilite .kc {{ color: #d73a49; font-weight: bold }} /* Keyword.Constant */
            .codehilite .kd {{ color: #d73a49; font-weight: bold }} /* Keyword.Declaration */
            .codehilite .kn {{ color: #d73a49; font-weight: bold }} /* Keyword.Namespace */
            .codehilite .kp {{ color: #d73a49; font-weight: bold }} /* Keyword.Pseudo */
            .codehilite .kr {{ color: #d73a49; font-weight: bold }} /* Keyword.Reserved */
            .codehilite .kt {{ color: #d73a49; font-weight: bold }} /* Keyword.Type */
            .codehilite .m {{ color: #005cc5 }} /* Literal.Number */
            .codehilite .s {{ color: #032f62 }} /* Literal.String */
            .codehilite .na {{ color: #005cc5 }} /* Name.Attribute */
            .codehilite .nb {{ color: #e36209 }} /* Name.Builtin */
            .codehilite .nc {{ color: #6f42c1; font-weight: bold }} /* Name.Class */
            .codehilite .no {{ color: #005cc5 }} /* Name.Constant */
            .codehilite .nd {{ color: #6f42c1; font-weight: bold }} /* Name.Decorator */
            .codehilite .ni {{ color: #6f42c1 }} /* Name.Entity */
            .codehilite .ne {{ color: #6f42c1; font-weight: bold }} /* Name.Exception */
            .codehilite .nf {{ color: #6f42c1; font-weight: bold }} /* Name.Function */
            .codehilite .nl {{ color: #6f42c1; font-weight: bold }} /* Name.Label */
            .codehilite .nn {{ color: #6f42c1 }} /* Name.Namespace */
            .codehilite .nt {{ color: #22863a }} /* Name.Tag */
            .codehilite .nv {{ color: #005cc5 }} /* Name.Variable */
            .codehilite .ow {{ color: #d73a49; font-weight: bold }} /* Operator.Word */
            .codehilite .w {{ color: #bbbbbb }} /* Text.Whitespace */
            .codehilite .mf {{ color: #005cc5 }} /* Literal.Number.Float */
            .codehilite .mh {{ color: #005cc5 }} /* Literal.Number.Hex */
            .codehilite .mi {{ color: #005cc5 }} /* Literal.Number.Integer */
            .codehilite .mo {{ color: #005cc5 }} /* Literal.Number.Oct */
            .codehilite .sb {{ color: #032f62 }} /* Literal.String.Backtick */
            .codehilite .sc {{ color: #032f62 }} /* Literal.String.Char */
            .codehilite .sd {{ color: #032f62 }} /* Literal.String.Doc */
            .codehilite .s2 {{ color: #032f62 }} /* Literal.String.Double */
            .codehilite .se {{ color: #032f62 }} /* Literal.String.Escape */
            .codehilite .sh {{ color: #032f62 }} /* Literal.String.Heredoc */
            .codehilite .si {{ color: #032f62 }} /* Literal.String.Interpol */
            .codehilite .sx {{ color: #032f62 }} /* Literal.String.Other */
            .codehilite .sr {{ color: #032f62 }} /* Literal.String.Regex */
            .codehilite .s1 {{ color: #032f62 }} /* Literal.String.Single */
            .codehilite .ss {{ color: #032f62 }} /* Literal.String.Symbol */
            .codehilite .bp {{ color: #e36209 }} /* Name.Builtin.Pseudo */
            .codehilite .vc {{ color: #005cc5 }} /* Name.Variable.Class */
            .codehilite .vg {{ color: #005cc5 }} /* Name.Variable.Global */
            .codehilite .vi {{ color: #005cc5 }} /* Name.Variable.Instance */
            .codehilite .il {{ color: #005cc5 }} /* Literal.Number.Integer.Long */
        </style>
        """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            {base_tag}
            {css}
        </head>
        <body>
            {content}
        </body>
        </html>
        """
    
    def center_window(self):
        """将窗口移动到屏幕中心"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        """关闭窗口前检查是否保存"""
        # 检查所有标签页是否有未保存的更改
        modified_tabs = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab.is_modified:
                modified_tabs.append(tab)
        
        if modified_tabs:
            reply = QMessageBox.question(
                self, "保存更改",
                f"有 {len(modified_tabs)} 个标签页包含未保存的更改，是否全部保存？",
                QMessageBox.StandardButton.SaveAll | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.SaveAll:
                for tab in modified_tabs:
                    tab.save_file()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = resource_path("Gemini_Generated_Image_t2ldymt2ldymt2ld.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    editor = MarkdownEditor()
    
    # 强制将窗口置于最前并激活
    editor.setWindowState(editor.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
    editor.raise_()
    editor.activateWindow()
    # 针对 Windows 的强力置顶技巧：短暂设置置顶标志再取消
    editor.setWindowFlags(editor.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    editor.show() # 需要重新调用 show 以应用 flag
    editor.setWindowFlags(editor.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
    editor.show()

    # 如果有命令行参数，尝试打开所有文件
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            if os.path.exists(file_path):
                # 检查是否是文件
                if os.path.isfile(file_path):
                    editor.open_file_in_tab(file_path, in_new_tab=True)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
