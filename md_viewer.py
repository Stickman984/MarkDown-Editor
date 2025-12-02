#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown文档查看器
一个简单而强大的Markdown文件查看器，支持Windows平台，支持多标签页和智能链接处理
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import markdown
from pathlib import Path
import webbrowser
import subprocess
import urllib.parse
from html.parser import HTMLParser

class MarkdownViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown 文档查看器")
        self.root.geometry("1000x700")
        
        # 最近打开的文件列表
        self.recent_files = []
        self.max_recent_files = 5
        
        # Notepad++路径
        self.notepadpp_path = r"C:\Program Files\Notepad++\notepad++.exe"
        
        # 创建UI
        self.create_menu()
        self.create_toolbar()
        self.create_main_area()
        self.create_statusbar()
        
        # 设置样式
        self.setup_styles()
        
        # 绑定快捷键
        self.bind_shortcuts()
        
        # 支持拖放
        self.setup_drag_drop()
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        # Notepad++路径
        self.notepadpp_path = r"C:\Program Files\Notepad++\notepad++.exe"
        
        # 创建UI
        self.create_menu()
        self.create_toolbar()
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件(F)", menu=file_menu)
        file_menu.add_command(label="新建标签页(N)", command=self.new_tab, accelerator="Ctrl+T")
        file_menu.add_command(label="打开(O)...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="关闭标签页(W)", command=self.close_current_tab, accelerator="Ctrl+W")
        file_menu.add_separator()
        
        # 最近文件子菜单
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近打开", menu=self.recent_menu)
        self.update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="退出(X)", command=self.root.quit, accelerator="Alt+F4")
        
        # 查看菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="查看(V)", menu=view_menu)
        view_menu.add_command(label="放大", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="缩小", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="重置缩放", command=self.zoom_reset, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_command(label="刷新", command=self.refresh, accelerator="F5")
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助(H)", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 新建标签页按钮
        btn_new_tab = ttk.Button(toolbar, text="➕ 新建", command=self.new_tab)
        btn_new_tab.pack(side=tk.LEFT, padx=2)
        
        # 打开按钮
        btn_open = ttk.Button(toolbar, text="📂 打开", command=self.open_file)
        btn_open.pack(side=tk.LEFT, padx=2)
        
        # 刷新按钮
        btn_refresh = ttk.Button(toolbar, text="🔄 刷新", command=self.refresh)
        btn_refresh.pack(side=tk.LEFT, padx=2)
        
        # 分隔符
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 缩放按钮
        btn_zoom_in = ttk.Button(toolbar, text="🔍+ 放大", command=self.zoom_in)
        btn_zoom_in.pack(side=tk.LEFT, padx=2)
        
        btn_zoom_out = ttk.Button(toolbar, text="🔍- 缩小", command=self.zoom_out)
        btn_zoom_out.pack(side=tk.LEFT, padx=2)
        
        btn_zoom_reset = ttk.Button(toolbar, text="⚖️ 重置", command=self.zoom_reset)
        btn_zoom_reset.pack(side=tk.LEFT, padx=2)
        
    def create_main_area(self):
        """创建主显示区域（带标签页）"""
        # 创建Notebook（标签页容器）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 创建初始标签页
        self.new_tab()
        
    def create_statusbar(self):
        """创建状态栏"""
        self.statusbar = ttk.Label(
            self.root,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
    def bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind('<Control-t>', lambda e: self.new_tab())
        self.root.bind('<Control-T>', lambda e: self.new_tab())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-O>', lambda e: self.open_file())
        self.root.bind('<Control-w>', lambda e: self.close_current_tab())
        self.root.bind('<Control-W>', lambda e: self.close_current_tab())
        self.root.bind('<F5>', lambda e: self.refresh())
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-equal>', lambda e: self.zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-0>', lambda e: self.zoom_reset())
        # 添加 Ctrl+滚轮缩放
        self.root.bind('<Control-MouseWheel>', self.on_global_mousewheel_zoom)
        
    def setup_drag_drop(self):
        """设置拖放支持"""
        pass
    
    def new_tab(self):
        """创建新标签页"""
        # 创建标签页框架
        tab_frame = ttk.Frame(self.notebook)
        
        # 创建自定义HTML显示组件
        html_view = MarkdownHtmlFrame(
            tab_frame,
            viewer=self  # 传递viewer引用以处理链接
        )
        # 设置初始内容
        html_view.set_html("<h1>欢迎使用 Markdown 查看器</h1><p>请打开一个 Markdown 文件开始使用。</p>")
        html_view.pack(fill=tk.BOTH, expand=True)
        
        # 存储标签页数据（先创建 tab_data，后面绑定事件时需要）
        tab_data = {
            'frame': tab_frame,
            'html_view': html_view,
            'current_file': None,
            'zoom_level': 1.0,
            'zoom_timer': None,  # 用于防抖动
            'md': markdown.Markdown(extensions=[
                'extra', 'codehilite', 'toc', 'fenced_code', 'tables', 'nl2br'
            ])
        }
        
        # 将数据存储在框架对象中
        tab_frame.tab_data = tab_data
        
        # 绑定Ctrl+滚轮缩放到 tab_frame（而不是 html_view，因为 tkinterweb 会拦截事件）
        tab_frame.bind("<Control-MouseWheel>", lambda e: self.on_mousewheel_zoom(e, tab_frame))
        # 同时绑定到 html_view，以防万一
        html_view.bind("<Control-MouseWheel>", lambda e: self.on_mousewheel_zoom(e, tab_frame))
        
        # 添加标签页
        self.notebook.add(tab_frame, text="新标签页")
        
        # 切换到新标签页
        self.notebook.select(tab_frame)
        
        return tab_frame
    
    def close_current_tab(self):
        """关闭当前标签页"""
        if self.notebook.index("end") > 1:  # 至少保留一个标签页
            current_tab = self.notebook.select()
            self.notebook.forget(current_tab)
        else:
            messagebox.showinfo("提示", "至少需要保留一个标签页")
    
    def get_current_tab_data(self):
        """获取当前标签页的数据"""
        current_tab = self.notebook.select()
        if current_tab:
            tab_frame = self.notebook.nametowidget(current_tab)
            return tab_frame.tab_data
        return None
    
    def on_tab_changed(self, event):
        """标签页切换事件处理"""
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data['current_file']:
            filename = tab_data['current_file']
            self.root.title(f"Markdown 文档查看器 - {os.path.basename(filename)}")
            self.statusbar.config(text=f"已加载: {filename}")
        else:
            self.root.title("Markdown 文档查看器")
            self.statusbar.config(text="就绪")
        
    def open_file(self, in_new_tab=False):
        """打开文件对话框"""
        filename = filedialog.askopenfilename(
            title="选择Markdown文件",
            filetypes=[
                ("Markdown文件", "*.md *.markdown *.mdown"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            if in_new_tab:
                self.new_tab()
            self.load_file(filename)
    
    def load_file(self, filename, in_new_tab=False):
        """加载并显示文件"""
        try:
            # 如果需要在新标签页打开
            if in_new_tab:
                self.new_tab()
            
            tab_data = self.get_current_tab_data()
            if not tab_data:
                return
            
            # 读取文件
            with open(filename, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 转换为HTML
            tab_data['md'].reset()
            html_content = tab_data['md'].convert(md_content)
            
            # 存储原始HTML以便缩放时使用
            tab_data['raw_html'] = html_content
            
            # 获取文件所在目录作为基准路径
            base_dir = os.path.dirname(filename)
            
            # 添加CSS样式
            styled_html = self.wrap_html(html_content, tab_data['zoom_level'], base_path=base_dir)
            
            # 显示HTML
            tab_data['html_view'].set_html(styled_html)
            
            # 更新状态
            tab_data['current_file'] = filename
            
            # 更新标签页标题
            tab_index = self.notebook.index(self.notebook.select())
            self.notebook.tab(tab_index, text=os.path.basename(filename))
            
            self.root.title(f"Markdown 文档查看器 - {os.path.basename(filename)}")
            self.statusbar.config(text=f"已加载: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件:\n{str(e)}")
    
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
            # 如果路径不存在，且不是绝对路径，尝试相对于当前文件解析
            if not os.path.exists(decoded_url) and not os.path.isabs(decoded_url):
                tab_data = self.get_current_tab_data()
                if tab_data and tab_data['current_file']:
                    base_dir = os.path.dirname(tab_data['current_file'])
                    decoded_url = os.path.normpath(os.path.join(base_dir, decoded_url))
            
            # 检查是否是本地文件或文件夹
            if os.path.exists(decoded_url):
                if os.path.isdir(decoded_url):
                    # 文件夹 - 使用资源管理器打开
                    os.startfile(decoded_url)
                    self.statusbar.config(text=f"已在资源管理器中打开: {decoded_url}")
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
                            self.statusbar.config(text=f"已在Notepad++中打开: {os.path.basename(decoded_url)}")
                        else:
                            # Notepad++不存在，使用系统默认程序
                            os.startfile(decoded_url)
                            self.statusbar.config(text=f"已打开: {os.path.basename(decoded_url)}")
                    else:
                        # 其他文件 - 使用系统默认程序
                        os.startfile(decoded_url)
                        self.statusbar.config(text=f"已打开: {os.path.basename(decoded_url)}")
            else:
                # 不是本地文件，可能是URL - 使用默认浏览器打开
                webbrowser.open(url)
                self.statusbar.config(text=f"已在浏览器中打开: {url}")
        
        except Exception as e:
            messagebox.showerror("错误", f"无法打开链接:\n{str(e)}")
            
    def wrap_html(self, content, zoom_level=1.0, base_path=None):
        """包装HTML内容并添加样式"""
        # 使用 font-size 缩放，同时用显式宽度缩放图片
        base_font_size = int(14 * zoom_level)
        
        # 计算缩放后的布局参数
        # 基础宽度 900px，随缩放比例调整
        container_width = int(900 * zoom_level)
        # 基础内边距 20px
        padding = int(20 * zoom_level)
        # 基础外边距 20px
        margin = int(20 * zoom_level)
        
        # 标题间距
        h_margin_top = int(24 * zoom_level)
        h_margin_bottom = int(16 * zoom_level)
        
        # 代码块内边距
        pre_padding = int(16 * zoom_level)
        
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
                font-size: {base_font_size}px;
                line-height: 1.6;
                color: #333;
                width: {container_width}px;  /* 使用固定宽度而不是 max-width，强制出现滚动条 */
                margin: {margin}px auto;
                padding: {padding}px;
                background-color: #fff;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: {h_margin_top}px;
                margin-bottom: {h_margin_bottom}px;
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
                padding: {pre_padding}px;
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
                margin: {h_margin_bottom}px 0;
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
            hr {{
                height: 0.25em;
                padding: 0;
                margin: {h_margin_top}px 0;
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
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data['current_file']:
            self.load_file(tab_data['current_file'])
            
    def update_zoom(self):
        """应用缩放"""
        tab_data = self.get_current_tab_data()
        if tab_data and 'raw_html' in tab_data:
            # 保存当前滚动位置（横向和纵向）
            scroll_y = 0.0
            scroll_x = 0.0
            scroll_x_center = False  # 标记是否需要横向居中
            
            try:
                # 访问底层的 html 组件来获取滚动位置
                if hasattr(tab_data['html_view'], 'html'):
                    # yview() 和 xview() 返回 (start, end) 元组
                    scroll_y = tab_data['html_view'].html.yview()[0]
                    x_view = tab_data['html_view'].html.xview()
                    scroll_x = x_view[0]
                    
                    # 如果当前横向可见范围是100%（没有横向滚动条），则需要在缩放后居中
                    if x_view[1] - x_view[0] >= 0.99:  # 允许一点误差
                        scroll_x_center = True
                        print(f"[DEBUG] Document is not scrollable horizontally, will center after zoom")
                    
                    print(f"[DEBUG] Saved scroll position: y={scroll_y:.4f}, x={scroll_x:.4f} (center={scroll_x_center})")
            except Exception as e:
                print(f"[DEBUG] Cannot get scroll position: {e}")
            
            base_dir = os.path.dirname(tab_data['current_file']) if tab_data['current_file'] else None
            styled_html = self.wrap_html(tab_data['raw_html'], tab_data['zoom_level'], base_path=base_dir)
            tab_data['html_view'].set_html(styled_html)
            
            # 定义恢复滚动位置的函数
            def restore_scroll(attempt_num=0):
                try:
                    if hasattr(tab_data['html_view'], 'html'):
                        # 恢复纵向位置
                        tab_data['html_view'].html.yview_moveto(scroll_y)
                        
                        # 处理横向位置
                        if scroll_x_center:
                            # 如果之前文档没有横向滚动条，现在需要居中
                            try:
                                x_view = tab_data['html_view'].html.xview()
                                # 计算居中位置：(1 - 可见范围) / 2
                                visible_range = x_view[1] - x_view[0]
                                if visible_range < 1.0:
                                    center_pos = (1.0 - visible_range) / 2.0
                                    tab_data['html_view'].html.xview_moveto(center_pos)
                                    print(f"[DEBUG] Attempt {attempt_num}: Centered horizontally at {center_pos:.4f}")
                                else:
                                    tab_data['html_view'].html.xview_moveto(0)
                                    print(f"[DEBUG] Attempt {attempt_num}: No horizontal scroll needed")
                            except Exception:
                                tab_data['html_view'].html.xview_moveto(scroll_x)
                        else:
                            # 恢复原来的横向位置
                            tab_data['html_view'].html.xview_moveto(scroll_x)
                            print(f"[DEBUG] Attempt {attempt_num}: Restored scroll to y={scroll_y:.4f}, x={scroll_x:.4f}")
                except Exception as e:
                    print(f"[DEBUG] Attempt {attempt_num}: Cannot restore scroll position: {e}")
            
            # 多次尝试恢复滚动位置，应对HTML渲染的不同阶段
            # 立即尝试一次
            self.root.after(1, lambda: restore_scroll(1))
            # 50ms后再尝试
            self.root.after(50, lambda: restore_scroll(2))
            # 150ms后最后尝试
            self.root.after(150, lambda: restore_scroll(3))

    def on_global_mousewheel_zoom(self, event):
        """处理全局 Ctrl+滚轮缩放"""  
        tab_data = self.get_current_tab_data()
        if tab_data:
            # Windows下，event.delta正数表示向上滚动（放大），负数表示向下滚动（缩小）
            if event.delta > 0:
                # 放大
                tab_data['zoom_level'] = min(tab_data['zoom_level'] + 0.1, 3.0)
            else:
                # 缩小
                tab_data['zoom_level'] = max(tab_data['zoom_level'] - 0.1, 0.2)
            
            self.update_zoom()

    def on_mousewheel_zoom(self, event, tab_frame):
        """处理Ctrl+滚轮缩放（带防抖动）"""
        tab_data = tab_frame.tab_data
        if tab_data:
            # 取消之前的缩放定时器（防抖动）
            if tab_data.get('zoom_timer'):
                self.root.after_cancel(tab_data['zoom_timer'])
            
            # Windows下，event.delta正数表示向上滚动（放大），负数表示向下滚动（缩小）
            # delta通常是120的倍数
            if event.delta > 0:
                # 放大
                tab_data['zoom_level'] = min(tab_data['zoom_level'] + 0.1, 3.0)
            else:
                # 缩小
                tab_data['zoom_level'] = max(tab_data['zoom_level'] - 0.1, 0.2)
            
            # 设置一个短延迟，避免快速滚动时多次触发
            # 只有在用户停止滚动100ms后才真正应用缩放
            def apply_zoom():
                tab_data['zoom_timer'] = None
                self.update_zoom()
            
            tab_data['zoom_timer'] = self.root.after(100, apply_zoom)

    def zoom_in(self):
        """放大"""
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data['zoom_level'] += 0.1
            self.update_zoom()
        
    def zoom_out(self):
        """缩小"""
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data['zoom_level'] > 0.2:
            tab_data['zoom_level'] -= 0.1
            self.update_zoom()
            
    def zoom_reset(self):
        """重置缩放"""
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data['zoom_level'] = 1.0
            self.update_zoom()
        
    def add_to_recent(self, filename):
        """添加到最近文件列表"""
        if filename in self.recent_files:
            self.recent_files.remove(filename)
        
        self.recent_files.insert(0, filename)
        
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        self.update_recent_menu()
        
    def update_recent_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.delete(0, tk.END)
        
        if self.recent_files:
            for i, filename in enumerate(self.recent_files, 1):
                self.recent_menu.add_command(
                    label=f"{i}. {os.path.basename(filename)}",
                    command=lambda f=filename: self.load_file(f, in_new_tab=False)
                )
        else:
            self.recent_menu.add_command(label="(无)", state=tk.DISABLED)
            
    def show_about(self):
        """显示关于对话框"""
        about_text = """
Markdown 文档查看器 v2.0

一个简洁实用的Markdown文件查看器

支持:
• 多标签页
• 标准Markdown语法
• 智能链接处理
• 表格、代码块
• 语法高亮
• 放大缩小

© 2025
        """
        messagebox.showinfo("关于", about_text.strip())






from tkinterweb import HtmlFrame

class MarkdownHtmlFrame(HtmlFrame):
    """基于tkinterweb的Markdown显示组件"""
    def __init__(self, master, viewer=None, **kwargs):
        self.viewer = viewer
        # 禁用默认的消息打印，并传入链接点击回调
        super().__init__(master, messages_enabled=False, on_link_click=self._handle_link_click, **kwargs)
        
    def _handle_link_click(self, url):
        """处理链接点击"""
        if self.viewer:
            self.viewer.handle_link_click(url)
        else:
            webbrowser.open(url)
            
    def set_html(self, html_content):
        """设置HTML内容"""
        # load_html是tkinterweb的方法
        self.load_html(html_content)



def main():
    """主函数"""
    root = tk.Tk()
    app = MarkdownViewer(root)
    
    # 如果有命令行参数，尝试打开第一个文件
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            app.load_file(file_path)
    
    root.mainloop()

if __name__ == "__main__":
    main()

