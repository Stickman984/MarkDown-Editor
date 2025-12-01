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
from tkhtmlview import HTMLScrolledText, html_parser
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
        
    def setup_drag_drop(self):
        """设置拖放支持"""
        pass
    
    def new_tab(self):
        """创建新标签页"""
        # 创建标签页框架
        tab_frame = ttk.Frame(self.notebook)
        
        # 创建自定义HTML显示组件
        html_view = CustomHTMLScrolledText(
            tab_frame,
            html="<h1>欢迎使用 Markdown 查看器</h1><p>请打开一个 Markdown 文件开始使用。</p>",
            wrap=tk.WORD,
            viewer=self  # 传递viewer引用以处理链接
        )
        html_view.pack(fill=tk.BOTH, expand=True)
        
        # 存储标签页数据
        tab_data = {
            'frame': tab_frame,
            'html_view': html_view,
            'current_file': None,
            'font_size': 12,
            'md': markdown.Markdown(extensions=[
                'extra', 'codehilite', 'toc', 'fenced_code', 'tables', 'nl2br'
            ])
        }
        
        # 将数据存储在框架对象中
        tab_frame.tab_data = tab_data
        
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
            
            # 添加CSS样式
            styled_html = self.wrap_html(html_content, tab_data['font_size'])
            
            # 显示HTML
            tab_data['html_view'].set_html(styled_html, strip=False)
            
            # 更新状态
            tab_data['current_file'] = filename
            
            # 更新标签页标题
            tab_index = self.notebook.index(self.notebook.select())
            self.notebook.tab(tab_index, text=os.path.basename(filename))
            
            self.root.title(f"Markdown 文档查看器 - {os.path.basename(filename)}")
            self.statusbar.config(text=f"已加载: {filename}")
            
            # 更新最近文件列表
            self.add_to_recent(filename)
            
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件:\n{str(e)}")
    
    def handle_link_click(self, url):
        """处理链接点击事件"""
        print(f"\n[DEBUG] ===== handle_link_click called =====")
        print(f"[DEBUG] Raw URL: {url}")
        
        try:
            # 解码URL
            decoded_url = urllib.parse.unquote(url)
            print(f"[DEBUG] Decoded URL: {decoded_url}")
            
            # 处理相对路径
            tab_data = self.get_current_tab_data()
            if tab_data and tab_data['current_file']:
                base_dir = os.path.dirname(tab_data['current_file'])
                # 如果是相对路径，转换为绝对路径
                if not os.path.isabs(decoded_url):
                    decoded_url = os.path.normpath(os.path.join(base_dir, decoded_url))
            
            # 检查是否是本地文件或文件夹
            print(f"[DEBUG] Checking if path exists: {decoded_url}")
            if os.path.exists(decoded_url):
                print(f"[DEBUG] Path exists!")
                if os.path.isdir(decoded_url):
                    # 文件夹 - 使用资源管理器打开
                    print(f"[DEBUG] Is directory, opening in Explorer")
                    os.startfile(decoded_url)
                    self.statusbar.config(text=f"已在资源管理器中打开: {decoded_url}")
                elif os.path.isfile(decoded_url):
                    # 文件 - 根据扩展名处理
                    ext = os.path.splitext(decoded_url)[1].lower()
                    print(f"[DEBUG] Is file, extension: {ext}")
                    if ext in ['.md', '.markdown', '.mdown']:
                        # Markdown文件 - 在新标签页打开
                        print(f"[DEBUG] Opening .md file in new tab")
                        self.load_file(decoded_url, in_new_tab=True)
                    elif ext in ['.txt', '.log', '.json', '.xml', '.yaml', '.yml', 
                                '.py', '.js', '.java', '.c', '.cpp', '.h', '.cs',
                                '.html', '.css', '.php', '.rb', '.go', '.rs', '.sh',
                                '.bat', '.ini', '.cfg', '.conf']:
                        # 文本文件 - 使用Notepad++打开
                        print(f"[DEBUG] Text file detected")
                        if os.path.exists(self.notepadpp_path):
                            print(f"[DEBUG] Opening with Notepad++: {self.notepadpp_path}")
                            subprocess.Popen([self.notepadpp_path, decoded_url])
                            self.statusbar.config(text=f"已在Notepad++中打开: {os.path.basename(decoded_url)}")
                        else:
                            # Notepad++不存在，使用系统默认程序
                            print(f"[DEBUG] Notepad++ not found, using startfile")
                            os.startfile(decoded_url)
                            self.statusbar.config(text=f"已打开: {os.path.basename(decoded_url)}")
                    else:
                        # 其他文件 - 使用系统默认程序
                        print(f"[DEBUG] Other file type, using startfile")
                        os.startfile(decoded_url)
                        self.statusbar.config(text=f"已打开: {os.path.basename(decoded_url)}")
            else:
                # 不是本地文件，可能是URL - 使用默认浏览器打开
                print(f"[DEBUG] Path does not exist, treating as URL")
                webbrowser.open(url)
                self.statusbar.config(text=f"已在浏览器中打开: {url}")
        
        except Exception as e:
            messagebox.showerror("错误", f"无法打开链接:\n{str(e)}")
            
    def wrap_html(self, content, font_size=12):
        """包装HTML内容并添加样式"""
        css = f"""
        <style>
            body {{
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
                font-size: {font_size}px;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 20px auto;
                padding: 20px;
                background-color: #fff;
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
                padding: 0.2em 0.4em;
                margin: 0;
                font-size: 85%;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            pre {{
                background-color: #f6f8fa;
                padding: 16px;
                overflow: auto;
                font-size: 85%;
                line-height: 1.45;
                border-radius: 3px;
            }}
            pre code {{
                background-color: transparent;
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
            
    def zoom_in(self):
        """放大"""
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data['font_size'] += 2
            self.refresh()
        
    def zoom_out(self):
        """缩小"""
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data['font_size'] > 8:
            tab_data['font_size'] -= 2
            self.refresh()
            
    def zoom_reset(self):
        """重置缩放"""
        tab_data = self.get_current_tab_data()
        if tab_data:
            tab_data['font_size'] = 12
            self.refresh()
        
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



class CustomHLinkSlot:
    """自定义链接槽，替换tkhtmlview的默认HLinkSlot"""
    def __init__(self, w, tag_name, url, viewer):
        self._w = w
        self.tag_name = tag_name
        self.URL = url
        self.viewer = viewer
        print(f"[DEBUG] CustomHLinkSlot created for URL: {url}")
    
    def call(self, event):
        """链接被点击时调用"""
        print(f"\n[DEBUG] ===== CustomHLinkSlot.call() triggered =====")
        print(f"[DEBUG] URL clicked: {self.URL}")
        
        if self.viewer:
            print(f"[DEBUG] Calling viewer.handle_link_click()")
            self.viewer.handle_link_click(self.URL)
        else:
            print(f"[DEBUG] No viewer, using webbrowser.open()")
            webbrowser.open(self.URL)
        
        # 改变链接颜色表示已访问
        self._w.tag_config(self.tag_name, foreground="purple")
    
    def enter(self, event):
        """鼠标进入链接区域"""
        self._w.config(cursor="hand2")
    
    def leave(self, event):
        """鼠标离开链接区域"""
        self._w.config(cursor="")


class CustomHTMLScrolledText(HTMLScrolledText):
    """自定义HTML显示组件，支持自定义链接处理"""
    def __init__(self, *args, viewer=None, **kwargs):
        self.viewer = viewer
        print("[DEBUG] CustomHTMLScrolledText.__init__ called")
        print(f"[DEBUG] viewer: {viewer}")
        super().__init__(*args, **kwargs)
        print("[DEBUG] CustomHTMLScrolledText initialized successfully")
    
    def set_html(self, html, strip=True):
        """重写set_html以替换链接处理器"""
        print(f"[DEBUG] CustomHTMLScrolledText.set_html called")
        
        # 先调用父类方法渲染HTML
        super().set_html(html, strip)
        
        # 替换所有的HLinkSlot为CustomHLinkSlot
        print(f"[DEBUG] Replacing link handlers...")
        if hasattr(self.html_parser, 'hlink_slots'):
            print(f"[DEBUG] Found {len(self.html_parser.hlink_slots)} link slots")
            
            # 保存原始的hlink_slots
            original_slots = self.html_parser.hlink_slots
            
            # 创建新的自定义链接槽列表
            custom_slots = []
            
            for slot in original_slots:
                # 获取原始slot的信息
                tag_name = slot.tag_name
                url = slot.URL
                
                print(f"[DEBUG] Replacing slot for tag={tag_name}, url={url}")
                
                # 创建自定义slot
                custom_slot = CustomHLinkSlot(self, tag_name, url, self.viewer)
                custom_slots.append(custom_slot)
                
                # 解绑原始事件
                self.tag_unbind(tag_name, "<Button-1>")
                self.tag_unbind(tag_name, "<Enter>")
                self.tag_unbind(tag_name, "<Leave>")
                
                # 绑定新的事件处理器
                self.tag_bind(tag_name, "<Button-1>", custom_slot.call)
                self.tag_bind(tag_name, "<Enter>", custom_slot.enter)
                self.tag_bind(tag_name, "<Leave>", custom_slot.leave)
            
            # 替换html_parser的hlink_slots
            self.html_parser.hlink_slots = custom_slots
            print(f"[DEBUG] Successfully replaced all {len(custom_slots)} link handlers")
        else:
            print(f"[DEBUG] WARNING: html_parser has no hlink_slots attribute")



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

