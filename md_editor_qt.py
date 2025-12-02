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
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QSplitter, QPlainTextEdit,
    QFileDialog, QMessageBox, QToolBar, QStatusBar, QWidget, QVBoxLayout
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt, QTimer, pyqtSlot
from PyQt6.QtGui import (
    QAction, QKeySequence, QSyntaxHighlighter, QTextCharFormat,
    QColor, QFont
)
import markdown


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown语法高亮器"""
    
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
    """自定义WebView用于预览"""
    
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
    """自定义WebEnginePage，用于拦截链接导航"""
    
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
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("在此输入Markdown内容...")
        
        # 设置编辑器字体
        font = QFont("Consolas", 11)
        self.editor.setFont(font)
        
        # 应用语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 监听文本变化
        self.editor.textChanged.connect(self.on_text_changed)
        
        # 创建预览
        self.preview = MarkdownWebView(self)
        
        # 添加到分割器
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        
        # 设置初始比例 (50:50)
        self.splitter.setSizes([600, 600])
        
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
        self.base_font_size = 11
        
        # 监听编辑器滚动
        self.editor.verticalScrollBar().valueChanged.connect(self.on_editor_scroll)
        
        # 安装事件过滤器以捕获Ctrl+滚轮缩放
        self.editor.installEventFilter(self)
        self.preview.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理Ctrl+滚轮缩放"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QWheelEvent
        
        if event.type() == QEvent.Type.Wheel and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            wheel_event = event
            delta = wheel_event.angleDelta().y()
            
            if obj == self.editor:
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
    
    def update_preview(self):
        """更新预览"""
        # 保存当前滚动位置（百分比）
        current_scroll_ratio = 0.0
        scrollbar = self.editor.verticalScrollBar()
        if scrollbar.maximum() > 0:
            current_scroll_ratio = scrollbar.value() / scrollbar.maximum()
        
        # 获取编辑器内容
        text = self.editor.toPlainText()
        
        # 转换为HTML
        self.main_window.md.reset()
        html_content = self.main_window.md.convert(text)
        
        # 获取baseUrl用于相对路径解析
        base_url = None
        if self.current_file:
            base_dir = os.path.dirname(self.current_file)
            base_url = QUrl.fromLocalFile(base_dir + "/")
        
        # 包装样式
        styled_html = self.main_window.wrap_html(
            html_content, 
            self.preview.zoom_level,
            base_path=os.path.dirname(self.current_file) if self.current_file else None
        )
        
        # 添加滚动监听脚本和自动恢复滚动位置脚本
        scroll_script = f"""
        <script>
        let scrollTimeout;
        window.addEventListener('scroll', function() {{
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
            var scrollRatio = {current_scroll_ratio};
            var scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            window.scrollTo(0, scrollHeight * scrollRatio);
        }});
        </script>
        """
        styled_html = styled_html.replace('</body>', scroll_script + '</body>')
        
        # 更新预览，提供baseUrl
        if base_url:
            self.preview.setHtml(styled_html, base_url)
        else:
            self.preview.setHtml(styled_html)
        
        # 设置标题变化监听（用于接收滚动数据）
        self.preview.page().titleChanged.connect(self.on_preview_title_changed)
    
    def on_preview_title_changed(self, title):
        """预览窗口标题改变时（用于接收滚动数据）"""
        if title.startswith('SCROLL:'):
            try:
                import json
                scroll_data = json.loads(title[7:])
                self.on_preview_scroll(scroll_data)
            except:
                pass
    
    def load_file(self, filename):
        """加载文件到此标签页"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.editor.setPlainText(content)
            self.current_file = filename
            self.is_modified = False
            self.main_window.update_tab_title(self)
            self.main_window.statusbar.showMessage(f"已打开: {filename}")
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"无法打开文件:\n{str(e)}")
    
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
        self.setGeometry(100, 100, 1200, 800)
        
        # Notepad++路径
        self.notepadpp_path = r"C:\Program Files\Notepad++\notepad++.exe"
        
        # Markdown转换器
        self.md = markdown.Markdown(extensions=[
            'extra', 'codehilite', 'toc', 'fenced_code', 'tables', 'nl2br'
        ])
        
        # 创建UI
        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()
        self.create_tab_widget()
        
        # 不自动创建标签页，用户可以手动打开文件或新建
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_tab_action = QAction("新建标签页(&T)", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_tab_action)
        
        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为(&A)...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction("关闭标签页(&W)", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        self.toggle_editor_action = QAction("隐藏编辑器", self)
        self.toggle_editor_action.triggered.connect(self.toggle_editor)
        view_menu.addAction(self.toggle_editor_action)
        
        self.toggle_preview_action = QAction("隐藏预览", self)
        self.toggle_preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(self.toggle_preview_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 标签页操作
        new_tab_action = QAction("📑 新标签页", self)
        new_tab_action.triggered.connect(self.new_tab)
        toolbar.addAction(new_tab_action)
        
        toolbar.addSeparator()
        
        # 文件操作
        new_action = QAction("📄 新建", self)
        new_action.triggered.connect(self.new_file)
        toolbar.addAction(new_action)
        
        open_action = QAction("📂 打开", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        save_action = QAction("💾 保存", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 视图切换
        toggle_editor_action = QAction("📝 编辑器", self)
        toggle_editor_action.triggered.connect(self.toggle_editor)
        toolbar.addAction(toggle_editor_action)
        
        toggle_preview_action = QAction("👁 预览", self)
        toggle_preview_action.triggered.connect(self.toggle_preview)
        toolbar.addAction(toggle_preview_action)
    
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
    
    def new_tab(self):
        """创建新标签页"""
        tab = EditorTab(self)
        
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
    
    def open_file_in_tab(self, filename, in_new_tab=False):
        """在标签页中打开文件"""
        if in_new_tab:
            self.new_tab()
        
        tab = self.get_current_tab()
        if tab:
            tab.load_file(filename)
    
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
                self.toggle_editor_action.setText("显示编辑器")
            else:
                tab.editor.show()
                self.toggle_editor_action.setText("隐藏编辑器")
    
    def toggle_preview(self):
        """切换预览显示/隐藏"""
        tab = self.get_current_tab()
        if tab:
            if tab.preview.isVisible():
                tab.preview.hide()
                self.toggle_preview_action.setText("显示预览")
            else:
                tab.preview.show()
                self.toggle_preview_action.setText("隐藏预览")
    
    def handle_link_click(self, url):
        """处理链接点击事件"""
        try:
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
                        self.open_file_in_tab(decoded_url, in_new_tab=True)
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
                font-size: 14px;
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
                background-color: #282c34;
                color: #abb2bf;
                padding: 0.2em 0.4em;
                margin: 0;
                font-size: 85%;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', 'Cascadia Code', monospace;
            }}
            pre {{
                background-color: #282c34;
                padding: 16px;
                overflow: auto;
                font-size: 85%;
                line-height: 1.45;
                border-radius: 6px;
                border: 1px solid #3e4451;
            }}
            pre code {{
                background-color: transparent;
                color: #abb2bf;
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
            hr {{
                height: 0.25em;
                padding: 0;
                margin: 24px 0;
                background-color: #e1e4e8;
                border: 0;
            }}
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
    
    editor = MarkdownEditor()
    editor.show()
    
    # 如果有命令行参数，尝试打开第一个文件
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            editor.open_file_in_tab(file_path)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
