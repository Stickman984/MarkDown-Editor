#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown文档查看器 - Qt版本
基于PyQt6和QWebEngineView，提供无闪烁的缩放体验
"""

import os
import sys
import subprocess
import webbrowser
import urllib.parse
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QFileDialog, 
    QMessageBox, QToolBar, QStatusBar, QWidget, QVBoxLayout
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence
import markdown


class MarkdownWebView(QWebEngineView):
    """自定义WebView，用于拦截链接点击"""
    
    def __init__(self, viewer, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        self.zoom_level = 1.0
        
        # 创建自定义页面以拦截链接
        self.page_obj = MarkdownWebPage(self)
        self.setPage(self.page_obj)
        
        # 启用一些设置
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    
    def set_zoom(self, zoom_level):
        """设置缩放级别（通过JavaScript）"""
        self.zoom_level = zoom_level
        # 使用JavaScript动态修改CSS zoom属性，无需重新加载页面
        js_code = f"document.body.style.zoom = {zoom_level};"
        self.page().runJavaScript(js_code)
    
    def set_html_content(self, html_content, base_url=None):
        """设置HTML内容"""
        if base_url:
            self.setHtml(html_content, QUrl.fromLocalFile(base_url + "/"))
        else:
            self.setHtml(html_content)


class MarkdownWebPage(QWebEnginePage):
    """自定义WebEnginePage，用于拦截链接导航"""
    
    def __init__(self, web_view):
        super().__init__(web_view)
        self.web_view = web_view
    
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        """拦截导航请求"""
        # 只处理用户点击的链接
        if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            # 阻止默认导航，交给viewer处理
            self.web_view.viewer.handle_link_click(url.toString())
            return False
        
        # 允许其他类型的导航（如初始加载）
        return True


class MarkdownViewerQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown 文档查看器 (Qt)")
        self.setGeometry(100, 100, 1000, 700)
        
        # 最近打开的文件列表
        self.recent_files = []
        self.max_recent_files = 5
        
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
        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()  # 先创建状态栏
        self.create_main_area()  # 后创建主区域，因为new_tab会触发on_tab_changed
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_tab_action = QAction("新建标签页(&N)", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_tab_action)
        
        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        close_tab_action = QAction("关闭标签页(&W)", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 查看菜单
        view_menu = menubar.addMenu("查看(&V)")
        
        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_reset_action = QAction("重置缩放", self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.triggered.connect(self.zoom_reset)
        view_menu.addAction(zoom_reset_action)
        
        view_menu.addSeparator()
        
        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh)
        view_menu.addAction(refresh_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 新建标签页按钮
        new_tab_action = QAction("➕ 新建", self)
        new_tab_action.triggered.connect(self.new_tab)
        toolbar.addAction(new_tab_action)
        
        # 打开按钮
        open_action = QAction("📂 打开", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        # 刷新按钮
        refresh_action = QAction("🔄 刷新", self)
        refresh_action.triggered.connect(self.refresh)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 缩放按钮
        zoom_in_action = QAction("🔍+ 放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔍- 缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        zoom_reset_action = QAction("⚖️ 重置", self)
        zoom_reset_action.triggered.connect(self.zoom_reset)
        toolbar.addAction(zoom_reset_action)
    
    def create_main_area(self):
        """创建主显示区域（带标签页）"""
        # 创建标签页容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.setCentralWidget(self.tab_widget)
        
        # 创建初始标签页
        self.new_tab()
    
    def create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
    
    def new_tab(self):
        """创建新标签页"""
        # 创建WebView
        web_view = MarkdownWebView(self)
        
        # 设置初始内容
        welcome_html = self.wrap_html("<h1>欢迎使用 Markdown 查看器 (Qt)</h1><p>请打开一个 Markdown 文件开始使用。</p>", 1.0)
        web_view.set_html_content(welcome_html)
        
        # 添加到标签页
        index = self.tab_widget.addTab(web_view, "新标签页")
        self.tab_widget.setCurrentIndex(index)
        
        # 存储标签页数据
        web_view.current_file = None
        web_view.raw_html = None
    
    def close_tab(self, index):
        """关闭指定标签页"""
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.information(self, "提示", "至少需要保留一个标签页")
    
    def close_current_tab(self):
        """关闭当前标签页"""
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)
    
    def get_current_web_view(self):
        """获取当前标签页的WebView"""
        return self.tab_widget.currentWidget()
    
    def on_tab_changed(self, index):
        """标签页切换事件"""
        web_view = self.get_current_web_view()
        if web_view and hasattr(web_view, 'current_file') and web_view.current_file:
            filename = web_view.current_file
            self.setWindowTitle(f"Markdown 文档查看器 (Qt) - {os.path.basename(filename)}")
            self.statusbar.showMessage(f"已加载: {filename}")
        else:
            self.setWindowTitle("Markdown 文档查看器 (Qt)")
            self.statusbar.showMessage("就绪")
    
    def open_file(self):
        """打开文件对话框"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择Markdown文件",
            "",
            "Markdown文件 (*.md *.markdown *.mdown);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filename:
            self.load_file(filename)
    
    def load_file(self, filename, in_new_tab=False):
        """加载并显示文件"""
        try:
            # 如果需要在新标签页打开
            if in_new_tab:
                self.new_tab()
            
            web_view = self.get_current_web_view()
            if not web_view:
                return
            
            # 读取文件
            with open(filename, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 转换为HTML
            self.md.reset()
            html_content = self.md.convert(md_content)
            
            # 存储原始HTML
            web_view.raw_html = html_content
            web_view.current_file = filename
            
            # 获取文件所在目录作为基准路径
            base_dir = os.path.dirname(filename)
            
            # 添加CSS样式
            styled_html = self.wrap_html(html_content, web_view.zoom_level, base_path=base_dir)
            
            # 显示HTML
            web_view.set_html_content(styled_html, base_dir)
            
            # 更新标签页标题
            current_index = self.tab_widget.currentIndex()
            self.tab_widget.setTabText(current_index, os.path.basename(filename))
            
            self.setWindowTitle(f"Markdown 文档查看器 (Qt) - {os.path.basename(filename)}")
            self.statusbar.showMessage(f"已加载: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")
    
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
            
            # Windows下，如果路径以 / 开头且包含 : (例如 /D:/path)，去掉开头的 /
            if os.name == 'nt' and decoded_url.startswith('/') and len(decoded_url) > 2 and decoded_url[2] == ':':
                decoded_url = decoded_url[1:]
            
            # 规范化路径分隔符
            decoded_url = os.path.normpath(decoded_url)
            
            # 处理相对路径
            web_view = self.get_current_web_view()
            if not os.path.exists(decoded_url) and not os.path.isabs(decoded_url):
                if web_view and hasattr(web_view, 'current_file') and web_view.current_file:
                    base_dir = os.path.dirname(web_view.current_file)
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
                        self.load_file(decoded_url, in_new_tab=True)
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
                white-space: pre-wrap;
                word-wrap: break-word;
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
                cursor: pointer;
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
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            li > pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
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
    
    def refresh(self):
        """刷新当前文件"""
        web_view = self.get_current_web_view()
        if web_view and hasattr(web_view, 'current_file') and web_view.current_file:
            self.load_file(web_view.current_file)
    
    def zoom_in(self):
        """放大"""
        web_view = self.get_current_web_view()
        if web_view:
            web_view.zoom_level = min(web_view.zoom_level + 0.1, 3.0)
            web_view.set_zoom(web_view.zoom_level)
    
    def zoom_out(self):
        """缩小"""
        web_view = self.get_current_web_view()
        if web_view and web_view.zoom_level > 0.2:
            web_view.zoom_level = max(web_view.zoom_level - 0.1, 0.2)
            web_view.set_zoom(web_view.zoom_level)
    
    def zoom_reset(self):
        """重置缩放"""
        web_view = self.get_current_web_view()
        if web_view:
            web_view.zoom_level = 1.0
            web_view.set_zoom(web_view.zoom_level)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
Markdown 文档查看器 v2.0 (Qt版本)

一个基于PyQt6的Markdown文件查看器

支持:
• 多标签页
• 标准Markdown语法
• 智能链接处理
• 表格、代码块
• 语法高亮
• 无闪烁缩放

© 2025
        """
        QMessageBox.about(self, "关于", about_text.strip())


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    viewer = MarkdownViewerQt()
    viewer.show()
    
    # 如果有命令行参数，尝试打开第一个文件
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            viewer.load_file(file_path)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
