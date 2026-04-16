import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

class CustomTitleBar(QWidget):
    """
    自定义扁平化标题栏，内部嵌套工具栏并包含原生的最小化、最大化和关闭按钮。
    """
    def __init__(self, parent, toolbar, logo_path=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # 模仿现代应用（如 VS Code）的标题栏高度
        self.setFixedHeight(44) 
        self.setStyleSheet("""
            CustomTitleBar {
                background-color: #f2f2f9; 
            }
        """)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 0, 0)
        self.layout.setSpacing(10)

        # 1. 应用 Logo
        self.logo_label = QLabel()
        self.logo_label.setToolTip("Tutu Markdown Editor")
        self.layout.addWidget(self.logo_label)
        
        if logo_path:
            self.set_logo(logo_path)


        # 2. 嵌入主工具栏
        if toolbar:
            # 移除工具栏自身的边框，让它无缝融合进标题栏
            toolbar.setStyleSheet(toolbar.styleSheet() + "\nQToolBar { border-bottom: none; background: transparent; }")
            self.layout.addWidget(toolbar)

        # 3. 弹簧 (推开右侧控件)
        self.layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # 4. 窗口控制按钮 (最小化、最大化、关闭)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(0)

        self.btn_min = self._create_control_button("—") # 最小化
        self.btn_min.clicked.connect(self.parent_window.showMinimized)
        
        self.btn_max = self._create_control_button("☐") # 最大化/还原
        self.btn_max.clicked.connect(self.toggle_maximize)
        
        self.btn_close = self._create_control_button("❌") # 关闭
        self.btn_close.clicked.connect(self.parent_window.close)
        self.btn_close.setStyleSheet("""
            QToolButton { border: none; padding: 0px 16px; background-color: transparent; font-family: "Segoe UI"; font-size: 14px;}
            QToolButton:hover { background-color: #e81123; color: white; }
            QToolButton:pressed { background-color: #f1707a; color: white; }
        """)

        control_layout.addWidget(self.btn_min)
        control_layout.addWidget(self.btn_max)
        control_layout.addWidget(self.btn_close)
        
        self.layout.addLayout(control_layout)

        # 拖拽状态
        self._start_pos = None

    def set_logo(self, logo_path):
        """动态更新 Logo 图片"""
        if os.path.exists(logo_path):
            logo_pix = QPixmap(logo_path).scaled(
                24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(logo_pix)

    def _create_control_button(self, text):
        btn = QToolButton()
        btn.setText(text)
        btn.setFixedSize(46, 44)
        btn.setStyleSheet("""
            QToolButton { border: none; background-color: transparent; font-family: "Segoe UI"; font-size: 14px; padding-bottom: 2px;}
            QToolButton:hover { background-color: #e5e5e5; }
            QToolButton:pressed { background-color: #cccccc; }
        """)
        return btn

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_max.setText("☐")
        else:
            self.parent_window.showMaximized()
            self.btn_max.setText("❐")

    # ----- 窗口拖动逻辑 -----
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._start_pos is not None:
            delta = event.globalPosition().toPoint() - self._start_pos
            if self.parent_window.isMaximized():
                # 如果最大化时拖拽，自动还原窗口
                self.toggle_maximize()
                # 计算居中位置还原
                geo = self.parent_window.geometry()
                geo.moveCenter(event.globalPosition().toPoint())
                geo.moveTop(0) # 保持在鼠标正下方
                self.parent_window.setGeometry(geo)
                
            self.parent_window.move(self.parent_window.pos() + delta)
            self._start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._start_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()
