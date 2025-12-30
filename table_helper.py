#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QSpinBox, QLabel, QToolBar, QMessageBox, QWidget,
    QComboBox, QFontComboBox, QColorDialog, QInputDialog, QApplication,
    QPlainTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QAction, QIcon
import re
import html.parser


class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入表格数据")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("请将Markdown或HTML表格代码粘贴到下方:"))
        
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("| Header 1 | Header 2 |\n| -------- | -------- |\n| Cell 1   | Cell 2   |")
        layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        self.btn_import = QPushButton("导入")
        self.btn_import.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
    def get_text(self):
        return self.text_edit.toPlainText()


class TableHelperDialog(QDialog):
    def __init__(self, parent=None, initial_content=None):
        super().__init__(parent)
        self.setWindowTitle("表格助手")
        self.resize(800, 600)
        
        # 主要布局
        layout = QVBoxLayout(self)
        
        # 工具栏
        self.create_toolbar()
        layout.addWidget(self.toolbar)
        
        # 表格控件
        self.table = QTableWidget(5, 5) # 默认5x5
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        
        self.btn_insert = QPushButton("插入表格")
        self.btn_insert.clicked.connect(self.accept)
        self.btn_insert.setDefault(True)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_insert)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
        
        # 初始化表格内容
        if initial_content and self.parse_content(initial_content):
            pass # 解析成功，表格已更新
        else:
            self.init_table_items()


    def create_toolbar(self):
        self.toolbar = QToolBar()
        
        # 行列操作
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 100)
        self.spin_rows.setValue(5)
        self.spin_rows.setSuffix(" 行")
        self.spin_rows.valueChanged.connect(self.update_rows)
        
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 100)
        self.spin_cols.setValue(5)
        self.spin_cols.setSuffix(" 列")
        self.spin_cols.valueChanged.connect(self.update_cols)
        
        self.toolbar.addWidget(QLabel("尺寸:"))
        self.toolbar.addWidget(self.spin_rows)
        self.toolbar.addWidget(self.spin_cols)
        
        self.toolbar.addSeparator()
        
        # 合并/拆分
        action_merge = QAction("合并单元格", self)
        action_merge.triggered.connect(self.merge_cells)
        self.toolbar.addAction(action_merge)
        
        action_split = QAction("拆分单元格", self)
        action_split.triggered.connect(self.split_cells)
        self.toolbar.addAction(action_split)
        
        self.toolbar.addSeparator()
        
        # 对齐方式
        action_align_left = QAction("居左", self)
        action_align_left.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        self.toolbar.addAction(action_align_left)
        
        action_align_center = QAction("居中", self)
        action_align_center.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignCenter))
        self.toolbar.addAction(action_align_center)
        
        action_align_right = QAction("居右", self)
        action_align_right.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        self.toolbar.addAction(action_align_right)
        
        self.toolbar.addSeparator()
        
        # 字体样式
        action_bold = QAction("加粗", self)
        action_bold.setCheckable(True)
        action_bold.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(action_bold)
        
        action_color = QAction("设置颜色", self)
        action_color.triggered.connect(self.set_color)
        self.toolbar.addAction(action_color)

        self.toolbar.addSeparator()

        action_paste = QAction("📋 导入表格...", self)
        action_paste.triggered.connect(self.import_from_clipboard)
        self.toolbar.addAction(action_paste)

    def init_table_items(self):
        """确保每个单元格都有Item对象"""
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                if self.table.item(r, c) is None:
                    self.table.setItem(r, c, QTableWidgetItem(f"Cell {r+1},{c+1}"))

    def update_rows(self, count):
        self.table.setRowCount(count)
        self.init_table_items()

    def update_cols(self, count):
        self.table.setColumnCount(count)
        self.init_table_items()

    def merge_cells(self):
        selected = self.table.selectedRanges()
        if not selected:
            return
        
        # 只处理第一个选择区域
        rect = selected[0]
        self.table.setSpan(rect.topRow(), rect.leftColumn(), rect.rowCount(), rect.columnCount())

    def split_cells(self):
        """拆分当前选中区域内的所有span"""
        selected_items = self.table.selectedItems()
        # 这种方式比较粗糙，更好的方式是获取选中区域覆盖的spans
        # 在PyQt中，直接设置span(1,1)即可取消合并? 
        # setSpan(row, col, 1, 1) to reset
        
        # 简单策略：遍历选中的每一个单元格，如果它是某个span的起始点，重置它
        # 或者遍历整个选择区域，重置所有span
        ranges = self.table.selectedRanges()
        for rect in ranges:
            for r in range(rect.topRow(), rect.bottomRow() + 1):
                for c in range(rect.leftColumn(), rect.rightColumn() + 1):
                    self.table.setSpan(r, c, 1, 1)

    def set_alignment(self, align):
        for item in self.table.selectedItems():
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)

    def toggle_bold(self):
        should_bold = False
        items = self.table.selectedItems()
        if not items:
            return
            
        # 检查第一个项的状态来决定是全部加粗还是取消
        if items[0].font().bold():
            should_bold = False
        else:
            should_bold = True
            
        font_weight = QFont.Weight.Bold if should_bold else QFont.Weight.Normal
        
        for item in items:
            font = item.font()
            font.setWeight(font_weight)
            item.setFont(font)


    def set_color(self):
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "选择颜色")
        if color.isValid():
            items = self.table.selectedItems()
            for item in items:
                item.setForeground(color)

    def import_from_clipboard(self):
        """导入表格内容"""
        dialog = ImportDialog(self)
        
        # 尝试自动填充剪贴板内容到对话框
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            dialog.text_edit.setPlainText(text)
            
        if dialog.exec():
            content = dialog.get_text()
            if self.parse_content(content):
                QMessageBox.information(self, "成功", "已导入表格数据")
            else:
                QMessageBox.warning(self, "失败", "无法识别表格内容")
        
    def parse_content(self, text):
        """尝试解析内容并填充表格"""
        text = text.strip()
        if not text:
            return False
            
        # 简单判断是HTML还是Markdown
        if text.lower().startswith('<table'):
            return self.parse_html_table(text)
        elif '|' in text:
            return self.parse_markdown_table(text)
        return False

    def parse_markdown_table(self, text):
        """解析Markdown管道表格"""
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False
            
        # 过滤分隔行 (---|---)
        rows_data = []
        for line in lines:
            if not line.strip():
                continue
            # 简单检查是否是分隔行
            if re.match(r'^\s*\|?\s*:?-+:?\s*\|', line):
                continue
                
            parts = line.strip().strip('|').split('|')
            rows_data.append([p.strip() for p in parts])
            
        if not rows_data:
            return False
            
        rows = len(rows_data)
        cols = max(len(r) for r in rows_data)
        
        self.spin_rows.setValue(rows)
        self.spin_cols.setValue(cols)
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        
        for r, row_data in enumerate(rows_data):
            for c, cell_text in enumerate(row_data):
                if c < cols:
                    self.table.setItem(r, c, QTableWidgetItem(cell_text))
        
        self.init_table_items() # 填充剩余空格
        return True

    def parse_html_table(self, text):
        """解析HTML表格"""
        try:
            class TableParser(html.parser.HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.in_table = False
                    self.in_row = False
                    self.in_cell = False
                    self.rows = []
                    self.current_row = []
                    self.current_cell_text = ""
                    self.current_attrs = {}
                    
                def handle_starttag(self, tag, attrs):
                    if tag == 'table':
                        self.in_table = True
                    elif tag == 'tr':
                        self.in_row = True
                        self.current_row = []
                    elif tag in ('td', 'th'):
                        self.in_cell = True
                        self.current_cell_text = ""
                        self.current_attrs = dict(attrs)
                        
                def handle_endtag(self, tag):
                    if tag == 'tr':
                        self.in_row = False
                        self.rows.append(self.current_row)
                    elif tag in ('td', 'th'):
                        self.in_cell = False
                        self.current_row.append({
                            'text': self.current_cell_text,
                            'rowspan': int(self.current_attrs.get('rowspan', 1)),
                            'colspan': int(self.current_attrs.get('colspan', 1)),
                            'style': self.current_attrs.get('style', '')
                        })
                        
                def handle_data(self, data):
                    if self.in_cell:
                        self.current_cell_text += data

            parser = TableParser()
            parser.feed(text)
            
            if not parser.rows:
                return False
                
            # 计算实际行列数（考虑colspan/rowspan）
            # 这比较复杂，简化处理先假设结构规整
            # 我们先设定一个足够大的表格，然后填充
            row_count = len(parser.rows)
            # 估算最大列数（第一行）
            col_count = 0
            for cell in parser.rows[0]:
                 col_count += cell['colspan']
            
            # 使用更动态的方式计算 dimensions would be better, but tricky
            # Let's adjust dynamically
            
            self.table.clear()
            self.spin_rows.setValue(row_count)
            self.spin_cols.setValue(col_count) # Approx
            self.table.setRowCount(row_count)
            self.table.setColumnCount(col_count)
            
            # 填充数据
            # 需要处理 rowspans 导致的偏移
            # grid matrix: True = occupied
            grid = [[False for _ in range(col_count * 2)] for _ in range(row_count)]
            
            for r, row_data in enumerate(parser.rows):
                current_c = 0
                for cell in row_data:
                    # 寻找下一个空闲位置
                    while current_c < len(grid[0]) and grid[r][current_c]:
                        current_c += 1
                    
                    if current_c >= self.table.columnCount():
                         self.spin_cols.setValue(current_c + 1)
                         self.table.setColumnCount(current_c + 1)
                    
                    # 填充内容
                    item = QTableWidgetItem(cell['text'])
                    self.table.setItem(r, current_c, item)
                    
                    # 解析样式
                    style = cell['style'].lower()
                    if 'font-weight: bold' in style:
                        f = item.font()
                        f.setBold(True)
                        item.setFont(f)
                    
                    # 标记占用
                    rs = cell['rowspan']
                    cs = cell['colspan']
                    
                    if rs > 1 or cs > 1:
                        self.table.setSpan(r, current_c, rs, cs)
                    
                    for i in range(rs):
                        for j in range(cs):
                            if r + i < row_count:
                                grid[r+i][current_c+j] = True
            
            self.init_table_items()
            return True
        except Exception as e:
            print(f"HTML Parse Error: {e}")
            return False

    def generate_content(self):
        """智能生成内容（Markdown或HTML）"""
        # 检查是否需要HTML
        need_html = False
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        
        for r in range(rows):
            for c in range(cols):
                # 检查合并
                if self.table.rowSpan(r, c) > 1 or self.table.columnSpan(r, c) > 1:
                    need_html = True
                    break
                    
                item = self.table.item(r, c)
                if item:
                    # 检查特殊样式（除了居左对齐，因为MD默认居左）
                    # Markdown支持 :---: (居中) ---: (居右)
                    # 字体颜色/大小必须HTML
                    font = item.font()
                    fg = item.foreground().color()
                    
                    # 只有当字体/颜色显式修改过才强制HTML (简单比较)
                    # 注意：Point Size 比较如果系统默认是9，那么需要宽容度，或者直接比较
                    # if font.pointSize() != self.default_font.pointSize() or font.family() != self.default_font.family():
                    # 这里为了简化，假设只要设置了font，通常就是要改
                    
                    # 颜色存在且不为黑/自动
                    has_color = fg.isValid() and (fg != Qt.GlobalColor.black and fg.name() != "#000000")
                    
                    if has_color:
                         need_html = True # 样式改变强制HTML
                         break
            if need_html:
                break
                
        if need_html:
            return self.generate_html()
        else:
            return self.generate_markdown()

    def generate_markdown(self):
        """生成Markdown管道表格"""
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        
        # 收集数据和计算宽度
        data = []
        col_widths = [0] * cols
        
        # 1. 获取所有文本并计算列宽
        for r in range(rows):
            row_data = []
            for c in range(cols):
                item = self.table.item(r, c)
                text = item.text().replace('|', '\\|') if item else ""
                
                # 处理换行
                text = text.replace('\n', '<br>')
                
                # 处理加粗 (Markdown Export)
                if item and item.font().bold():
                     text = f"**{text}**"
                
                row_data.append(text)
                
                # 计算显示宽度
                # 中文字符宽度处理比较麻烦，这里简单估算：len(text.encode('utf-8')) * 0.7
                # 准确对其并不影响Markdown解析，只影响源码可读性
                col_widths[c] = max(col_widths[c], len(text) * 2) 
            data.append(row_data)
            
        # 最小宽度
        col_widths = [max(w, 5) for w in col_widths]
        
        lines = []
        
        # 2. 表头（第一行）
        header_contents = []
        for c in range(cols):
             header_contents.append(data[0][c].ljust(col_widths[c]))
        lines.append(f"| {' | '.join(header_contents)} |")
        
        # 3. 分隔行（处理对齐）
        sep_contents = []
        for c in range(cols):
            # 检查该列第一行的对齐方式
            item = self.table.item(0, c)
            align = item.textAlignment() if item else Qt.AlignmentFlag.AlignLeft
            
            # 默认居左 :---
            # 居右 ---:
            # 居中 :---:
            
            w = col_widths[c]
            if align & Qt.AlignmentFlag.AlignRight:
                 sep = "-" * (w - 1) + ":" 
            elif align & Qt.AlignmentFlag.AlignHCenter:
                 sep = ":" + "-" * (w - 2) + ":"
            else:
                 sep = "-" * w # Default Left, standard markdown often uses just dashes or :---
            
            sep_contents.append(sep)
            
        lines.append(f"| {' | '.join(sep_contents)} |")
        
        # 4. 数据行
        for r in range(1, rows):
            row_contents = []
            for c in range(cols):
                row_contents.append(data[r][c].ljust(col_widths[c]))
            lines.append(f"| {' | '.join(row_contents)} |")
            
        return "\n".join(lines)

    def generate_html(self):
        """生成HTML表格代码"""
        html = ["<table border='1' style='border-collapse: collapse; width: 100%;'>"]
        
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        
        # 记录已处理（被合并）的单元格
        covered = set()
        
        for r in range(rows):
            html.append("  <tr>")
            for c in range(cols):
                if (r, c) in covered:
                    continue
                
                # 获取span信息
                row_span = self.table.rowSpan(r, c)
                col_span = self.table.columnSpan(r, c)
                
                # 标记被覆盖的区域
                if row_span > 1 or col_span > 1:
                    for i in range(row_span):
                        for j in range(col_span):
                            if i == 0 and j == 0:
                                continue
                            covered.add((r + i, c + j))
                
                item = self.table.item(r, c)
                text = item.text() if item else ""
                
                # 构建属性
                attrs = []
                if row_span > 1:
                    attrs.append(f"rowspan='{row_span}'")
                if col_span > 1:
                    attrs.append(f"colspan='{col_span}'")
                
                # 样式
                styles = []
                if item:
                    # 对齐
                    align = item.textAlignment()
                    if align & Qt.AlignmentFlag.AlignLeft:
                        styles.append("text-align: left")
                    elif align & Qt.AlignmentFlag.AlignRight:
                        styles.append("text-align: right")
                    elif align & Qt.AlignmentFlag.AlignHCenter:
                        styles.append("text-align: center")
                    
                    # 字体加粗/样式
                    font = item.font()
                    if font.bold():
                        styles.append("font-weight: bold")
                    if font.italic():
                        styles.append("font-style: italic")
                    if font.underline():
                        styles.append("text-decoration: underline")
                    
                    # 文本颜色
                    fg = item.foreground().color()
                    if fg.isValid() and (fg != Qt.GlobalColor.black and fg.name() != "#000000"):
                        styles.append(f"color: {fg.name()}")
                        
                if styles:
                    attrs.append(f"style='{'; '.join(styles)}'")
                
                html.append(f"    <td {' '.join(attrs)}>{text}</td>")
            html.append("  </tr>")
            
        html.append("</table>")
        return "\n".join(html)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dialog = TableHelperDialog()
    if dialog.exec():
        print(dialog.generate_html())
