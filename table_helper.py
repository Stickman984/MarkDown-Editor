#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QSpinBox, QLabel, QToolBar, QMessageBox, QWidget,
    QComboBox, QFontComboBox, QColorDialog, QInputDialog, QApplication,
    QPlainTextEdit, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QAction, QIcon, QKeySequence
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
        self.resize(1100, 650)
        
        # 主要布局
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        
        # 工具栏
        self.create_toolbar()
        layout.addWidget(self.toolbar1)
        layout.addWidget(self.toolbar2)
        
        # 表格控件
        self.table = QTableWidget(5, 5) # 默认5x5
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
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
        
        
        # 初始化撤销重做支持
        self.undo_stack = []
        self.redo_stack = []
        self._is_restoring = False
        
        # 动态绑定所有会修改表格的操作方法到撤销记录器
        for method_name in [
            'update_rows', 'update_cols', 'insert_row_above', 'insert_row_below',
            'delete_selected_rows', 'insert_col_left', 'insert_col_right',
            'delete_selected_cols', 'merge_cells', 'split_cells', 'set_alignment',
            'toggle_bold', 'set_color', 'import_from_clipboard'
        ]:
            if hasattr(self, method_name):
                setattr(self, method_name, self.make_undoable(getattr(self, method_name)))

        # 初始化表格内容
        if initial_content and self.parse_content(initial_content):
            pass # 解析成功，表格已更新
        else:
            self.init_table_items()
            
        self.current_state = self.snapshot_state()
        self.table.itemChanged.connect(self.on_item_changed)


    def create_toolbar(self):
        # 统一使用更现代的 Office 风格样式
        toolbar_style = """
            QToolBar {
                background-color: #f3f2f1;
                border-bottom: 1px solid #e1dfdd;
                padding: 4px;
                spacing: 8px;
            }
            QToolButton {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 13px;
            }
            QToolButton:hover {
                background-color: #e1dfdd;
            }
            QLabel {
                font-weight: bold;
                color: #323130;
                padding-left: 8px;
                padding-right: 4px;
            }
        """
        
        # 第一行：基础属性与格式 (尺寸、合并、对齐、字体)
        self.toolbar1 = QToolBar()
        self.toolbar1.setMovable(False)
        self.toolbar1.setStyleSheet(toolbar_style)
        
        # --- 撤销/重做 ---
        self.action_undo = QAction("撤销", self)
        self.action_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self.action_undo.triggered.connect(self.perform_undo)
        self.action_undo.setEnabled(False)
        self.toolbar1.addAction(self.action_undo)
        
        self.action_redo = QAction("重做", self)
        self.action_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.action_redo.triggered.connect(self.perform_redo)
        self.action_redo.setEnabled(False)
        self.toolbar1.addAction(self.action_redo)
        self.toolbar1.addSeparator()
        
        # --- 尺寸组 ---
        self.toolbar1.addWidget(QLabel("📏 尺寸:"))
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
        
        self.toolbar1.addWidget(self.spin_rows)
        self.toolbar1.addWidget(self.spin_cols)
        self.toolbar1.addSeparator()
        
        # --- 对齐与样式 ---
        self.toolbar1.addWidget(QLabel("📝 格式:"))
        
        # 对齐
        action_align_left = QAction("居左", self)
        action_align_left.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        self.toolbar1.addAction(action_align_left)
        
        action_align_center = QAction("居中", self)
        action_align_center.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignCenter))
        self.toolbar1.addAction(action_align_center)
        
        action_align_right = QAction("居右", self)
        action_align_right.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        self.toolbar1.addAction(action_align_right)
        
        # 字体
        action_bold = QAction("加粗", self)
        action_bold.setCheckable(True)
        action_bold.triggered.connect(self.toggle_bold)
        self.toolbar1.addAction(action_bold)
        
        action_color = QAction("🎨 颜色", self)
        action_color.triggered.connect(self.set_color)
        self.toolbar1.addAction(action_color)
        
        # 导入按钮放到右侧
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Policy.Expanding, spacer.sizePolicy().Policy.Preferred)
        self.toolbar1.addWidget(spacer)
        
        action_paste = QAction("📋 导入表格数据...", self)
        action_paste.triggered.connect(self.import_from_clipboard)
        self.toolbar1.addAction(action_paste)

        # 第二行：单元格级结构操作 (合并拆分、行列增删)
        self.toolbar2 = QToolBar()
        self.toolbar2.setMovable(False)
        self.toolbar2.setStyleSheet(toolbar_style)
        
        # --- 合并/拆分 ---
        self.toolbar2.addWidget(QLabel("🔗 结构:"))
        action_merge = QAction("合并单元格", self)
        action_merge.triggered.connect(self.merge_cells)
        self.toolbar2.addAction(action_merge)
        
        action_split = QAction("拆分单元格", self)
        action_split.triggered.connect(self.split_cells)
        self.toolbar2.addAction(action_split)
        self.toolbar2.addSeparator()
        
        # --- 行列操作 ---
        self.toolbar2.addWidget(QLabel("➕ 行操作:"))
        action_insert_row_up = QAction("↑ 上插行", self)
        action_insert_row_up.triggered.connect(self.insert_row_above)
        self.toolbar2.addAction(action_insert_row_up)

        action_insert_row_down = QAction("↓ 下插行", self)
        action_insert_row_down.triggered.connect(self.insert_row_below)
        self.toolbar2.addAction(action_insert_row_down)

        action_del_row = QAction("❌ 删行", self)
        action_del_row.triggered.connect(self.delete_selected_rows)
        self.toolbar2.addAction(action_del_row)
        
        self.toolbar2.addSeparator()
        
        self.toolbar2.addWidget(QLabel("➕ 列操作:"))
        action_insert_col_left = QAction("← 左插列", self)
        action_insert_col_left.triggered.connect(self.insert_col_left)
        self.toolbar2.addAction(action_insert_col_left)

        action_insert_col_right = QAction("→ 右插列", self)
        action_insert_col_right.triggered.connect(self.insert_col_right)
        self.toolbar2.addAction(action_insert_col_right)

        action_del_col = QAction("❌ 删列", self)
        action_del_col.triggered.connect(self.delete_selected_cols)
        self.toolbar2.addAction(action_del_col)

        # ---------------- 颜色主题应用 ----------------
        # 格式化组 (蓝)
        for act in [action_align_left, action_align_center, action_align_right, action_bold, action_color]:
            self._style_action(self.toolbar1, act, "#e8f0fe", "#1a73e8", "#d2e3fc")
            
        # 结构组 (黄)
        for act in [action_merge, action_split]:
            self._style_action(self.toolbar2, act, "#fef7e0", "#b06000", "#fce8b2")
            
        # 插入行列组 (绿)
        for act in [action_insert_row_up, action_insert_row_down, action_insert_col_left, action_insert_col_right]:
            self._style_action(self.toolbar2, act, "#e6f4ea", "#137333", "#ceead6")
            
        # 删除行列组 (红)
        for act in [action_del_row, action_del_col]:
            self._style_action(self.toolbar2, act, "#fce8e6", "#c5221f", "#fad2cf")
            
        # 导入按钮 (强调紫)
        self._style_action(self.toolbar1, action_paste, "#f3e8fd", "#681da8", "#e9d2fc")
        
        # 撤销重做 (青色)
        for act in [self.action_undo, self.action_redo]:
            self._style_action(self.toolbar1, act, "#e0f7fa", "#006064", "#b2ebf2")

    def _style_action(self, toolbar, action, bg_color, text_color, hover_color):
        """给工具栏中特定 Action 的按钮设置颜色样式"""
        btn = toolbar.widgetForAction(action)
        if btn:
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 13px;
                }}
                QToolButton:hover {{
                    background-color: {hover_color};
                }}
            """)
            
    # ========================== 撤销/重做 快照机制 ==========================
    
    def snapshot_state(self):
        state = {
            'rows': self.table.rowCount(),
            'cols': self.table.columnCount(),
            'cells': []
        }
        for r in range(state['rows']):
            for c in range(state['cols']):
                item = self.table.item(r, c)
                if item:
                    font = item.font()
                    fg = item.foreground().color()
                    state['cells'].append({
                        'r': r, 'c': c,
                        'text': item.text(),
                        'align': int(item.textAlignment()),
                        'bold': font.bold(),
                        'color': fg.name() if fg.isValid() else None,
                        'rowspan': self.table.rowSpan(r, c),
                        'colspan': self.table.columnSpan(r, c)
                    })
        return state

    def restore_state(self, state):
        self._is_restoring = True
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setRowCount(state['rows'])
        self.table.setColumnCount(state['cols'])
        self._sync_spin_boxes()

        spans_to_set = []
        for cell in state['cells']:
            r, c = cell['r'], cell['c']
            item = QTableWidgetItem(cell['text'])
            item.setTextAlignment(Qt.AlignmentFlag(cell['align']))
            if cell['bold']:
                f = item.font()
                f.setBold(True)
                item.setFont(f)
            if cell['color']:
                item.setForeground(QColor(cell['color']))
            self.table.setItem(r, c, item)
            
            rs, cs = cell.get('rowspan', 1), cell.get('colspan', 1)
            if rs > 1 or cs > 1:
                spans_to_set.append((r, c, rs, cs))
                
        for span in spans_to_set:
            self.table.setSpan(*span)

        self.table.blockSignals(False)
        self._is_restoring = False

    def save_undo_state(self):
        if getattr(self, '_is_restoring', False):
            return
        if not hasattr(self, 'current_state'):
            return
        self.undo_stack.append(self.current_state)
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.update_action_states()

    def update_current_state(self):
        if getattr(self, '_is_restoring', False):
            return
        self.current_state = self.snapshot_state()

    def perform_undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.current_state)
        state = self.undo_stack.pop()
        self.restore_state(state)
        self.current_state = state
        self.update_action_states()

    def perform_redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.current_state)
        state = self.redo_stack.pop()
        self.restore_state(state)
        self.current_state = state
        self.update_action_states()

    def update_action_states(self):
        self.action_undo.setEnabled(len(self.undo_stack) > 0)
        self.action_redo.setEnabled(len(self.redo_stack) > 0)

    def on_item_changed(self, item):
        """处理直接的手动输入修改"""
        if getattr(self, '_is_restoring', False):
            return
        # 手动输入一个字母后，立刻快照
        self.save_undo_state()
        self.update_current_state()

    def make_undoable(self, func):
        """装饰器：将一个修改功能封装为支持状态快照的撤销步"""
        import inspect
        sig = inspect.signature(func)
        def wrapper(*args, **kwargs):
            # 避免 Qt 信号（如 Action.triggered 的 checked 标记）强行传入不需要参数的函数
            num_params = len([p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])
            valid_args = args[:num_params]
            
            if getattr(self, '_is_restoring', False):
                return func(*valid_args, **kwargs)
            self.save_undo_state()
            self._is_restoring = True
            try:
                res = func(*valid_args, **kwargs)
            finally:
                self._is_restoring = False
                self.update_current_state()
            return res
        return wrapper
        
    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        # 现代扁平化菜单样式
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d2d0ce;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 32px 8px 24px;
                color: #323130;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #f3f2f1;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e1dfdd;
                margin: 4px 0px;
            }
        """)
        
        # 行操作子菜单/项
        action_row_up = menu.addAction("🔼 向上插入行")
        action_row_up.triggered.connect(self.insert_row_above)
        
        action_row_down = menu.addAction("🔽 向下插入行")
        action_row_down.triggered.connect(self.insert_row_below)
        
        action_row_del = menu.addAction("❌ 删除选中行")
        action_row_del.triggered.connect(self.delete_selected_rows)
        
        menu.addSeparator()
        
        # 列操作
        action_col_left = menu.addAction("◀️ 向左插入列")
        action_col_left.triggered.connect(self.insert_col_left)
        
        action_col_right = menu.addAction("▶️ 向右插入列")
        action_col_right.triggered.connect(self.insert_col_right)
        
        action_col_del = menu.addAction("❌ 删除选中列")
        action_col_del.triggered.connect(self.delete_selected_cols)
        
        menu.addSeparator()
        
        # 单元格格式
        action_merge = menu.addAction("🔗 合并单元格")
        action_merge.triggered.connect(self.merge_cells)
        
        action_split = menu.addAction("✂️ 拆分单元格")
        action_split.triggered.connect(self.split_cells)
        
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def init_table_items(self):
        """确保每个单元格都有Item对象，默认为空"""
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                if self.table.item(r, c) is None:
                    self.table.setItem(r, c, QTableWidgetItem(""))

    def update_rows(self, count):
        self.table.setRowCount(count)
        self.init_table_items()

    def update_cols(self, count):
        self.table.setColumnCount(count)
        self.init_table_items()

    def insert_row_above(self):
        curr = self.table.currentRow()
        idx = max(0, curr)
        self.table.insertRow(idx)
        self._sync_spin_boxes()
        self.init_table_items()

    def insert_row_below(self):
        curr = self.table.currentRow()
        idx = curr + 1 if curr >= 0 else self.table.rowCount()
        self.table.insertRow(idx)
        self._sync_spin_boxes()
        self.init_table_items()

    def delete_selected_rows(self):
        rows = set()
        for r in self.table.selectedRanges():
            for i in range(r.topRow(), r.bottomRow() + 1):
                rows.add(i)
        
        if not rows:
            return
            
        for r in sorted(list(rows), reverse=True):
            self.table.removeRow(r)
        
        self._sync_spin_boxes()

    def insert_col_left(self):
        curr = self.table.currentColumn()
        idx = max(0, curr)
        self.table.insertColumn(idx)
        self._sync_spin_boxes()
        self.init_table_items()

    def insert_col_right(self):
        curr = self.table.currentColumn()
        idx = curr + 1 if curr >= 0 else self.table.columnCount()
        self.table.insertColumn(idx)
        self._sync_spin_boxes()
        self.init_table_items()

    def delete_selected_cols(self):
        cols = set()
        for r in self.table.selectedRanges():
            for i in range(r.leftColumn(), r.rightColumn() + 1):
                cols.add(i)
        
        if not cols:
            return
            
        for c in sorted(list(cols), reverse=True):
            self.table.removeColumn(c)
        
        self._sync_spin_boxes()

    def _sync_spin_boxes(self):
        self.spin_rows.blockSignals(True)
        self.spin_rows.setValue(self.table.rowCount())
        self.spin_rows.blockSignals(False)
        
        self.spin_cols.blockSignals(True)
        self.spin_cols.setValue(self.table.columnCount())
        self.spin_cols.blockSignals(False)

    def _get_visual_width(self, text):
        """估算文本的视觉宽度 (CJK字符计为2，其他计为1)"""
        width = 0
        for char in text:
            if ord(char) > 127:
                width += 2
            else:
                width += 1
        return width

    def _visual_ljust(self, text, width):
        """按视觉宽度进行左对齐填充"""
        current_width = self._get_visual_width(text)
        if current_width >= width:
            return text
        return text + " " * (width - current_width)

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
                # 准确对其并不影响Markdown解析，只影响源码可读性
                col_widths[c] = max(col_widths[c], self._get_visual_width(text))
            data.append(row_data)
            
        # 最小宽度
        col_widths = [max(w, 5) for w in col_widths]
        
        lines = []
        
        # 2. 表头（第一行）
        header_contents = []
        for c in range(cols):
             header_contents.append(self._visual_ljust(data[0][c], col_widths[c]))
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
                row_contents.append(self._visual_ljust(data[r][c], col_widths[c]))
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
