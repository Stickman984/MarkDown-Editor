#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QSpinBox, QLabel, QToolBar, QMessageBox, QWidget,
    QComboBox, QFontComboBox, QColorDialog, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QAction, QIcon

class TableHelperDialog(QDialog):
    def __init__(self, parent=None):
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
        
        action_font = QAction("设置字体", self)
        action_font.triggered.connect(self.set_font)
        self.toolbar.addAction(action_font)

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

    def set_font(self):
        from PyQt6.QtWidgets import QFontDialog
        
        # 获取当前选中项的字体作为初始值
        current_font = QFont()
        items = self.table.selectedItems()
        if items:
            current_font = items[0].font()
            
        ok, font = QFontDialog.getFont(current_font, self)
        if ok:
            for item in items:
                item.setFont(font)
        
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
                    
                    # 只有当字体属性显式修改过才通过style输出，避免默认字体污染
                    # 这里比较难判断是否修改过，简单起见，如果设置了特定字体，就输出
                    # 我们可以通过比较默认字体和item字体
                    # 但QFontDialog返回的字体通常带有具体属性
                    # 这里我们输出 font-family 和 font-size
                    styles.append(f"font-family: '{font.family()}'")
                    styles.append(f"font-size: {font.pointSize()}pt")
                        
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
