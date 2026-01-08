import os
import re
from PyQt6.QtWidgets import QCompleter
from PyQt6.QtCore import Qt, QRect, QDir, QStringListModel

class PathCompleter(QCompleter):
    """
    专门用于处理文件路径补全的 QCompleter
    使用 QStringListModel 和 os.listdir 以获得更好的兼容性
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        # 使用 QStringListModel，由我们手动提取目录内容
        self.model = QStringListModel(self)
        self.setModel(self.model)
        
        # 记录基准目录（当前编辑文件所在的目录）
        self.base_dir = ""
        
    def set_base_dir(self, base_dir):
        """设置补全的基准目录"""
        if base_dir and os.path.isdir(base_dir):
            self.base_dir = base_dir

    def extract_path_prefix(self, text_before_cursor):
        """
        从光标前的文本中提取路径前缀
        例如: text="[link](./files/" -> return "./files/"
        """
        # 匹配 Markdown 链接或图片中的路径部分
        # 匹配 [...](path 或 ![...](path
        # 也可以支持直接输入路径的情景
        
        # 寻找最近的 ( 或 [
        match = re.search(r'[\(\[]([^\(\[\]\)]*)$', text_before_cursor)
        if match:
            path_part = match.group(1)
            # 只有当路径是以 . 或 / 开头，或者包含 / 时才触发
            if path_part.startswith(('.', '/')) or '/' in path_part:
                return path_part
        return None

    def update_completion_prefix(self, path_prefix):
        """根据提取的路径前缀更新补全模型"""
        if not path_prefix:
            return False

        # 处理相对路径
        full_path_prefix = path_prefix
        if path_prefix.startswith('.'):
            full_path_prefix = os.path.normpath(os.path.join(self.base_dir, path_prefix))
        elif not os.path.isabs(path_prefix):
            # 假设相对于 base_dir
            full_path_prefix = os.path.normpath(os.path.join(self.base_dir, path_prefix))

        # 区分 目录部分 和 正在输入的文件名部分
        if path_prefix.endswith(('/', '\\')):
            dir_path = full_path_prefix
            file_prefix = ""
        else:
            dir_path = os.path.dirname(full_path_prefix)
            file_prefix = os.path.basename(full_path_prefix)

        if os.path.isdir(dir_path):
            try:
                # 获取目录下的所有项
                items = os.listdir(dir_path)
                # 过滤掉隐藏文件 (可选，这里根据需要包含)
                # items = [i for i in items if not i.startswith('.')]
                self.model.setStringList(items)
                self.setCompletionPrefix(file_prefix)
                return True
            except Exception:
                return False
        
        return False

    def insert_completion(self, completion, text_edit):
        """将选中的补全项插入到编辑器"""
        if self.widget() != text_edit:
            return

        # 使用临时光标获取光标之前的文本，不影响真实光标位置
        temp_cursor = text_edit.textCursor()
        temp_cursor.movePosition(temp_cursor.MoveOperation.StartOfLine, temp_cursor.MoveMode.KeepAnchor)
        line_text = temp_cursor.selectedText()
        
        # 获取当前的真实光标（插入点）
        cursor = text_edit.textCursor()
        
        path_prefix = self.extract_path_prefix(line_text)
        if path_prefix is None:
            return

        # 计算要替换的字符数
        # 我们只替换正在输入的文件名部分，或者追加
        if path_prefix.endswith(('/', '\\')):
            # 追加
            cursor.insertText(completion)
        else:
            # 替换最后一部分（自最后一个斜杠之后的内容）
            last_slash_idx = max(path_prefix.rfind('/'), path_prefix.rfind('\\'))
            # file_prefix 是光标前正在输入的部分
            file_prefix = path_prefix[last_slash_idx + 1:]
            # 回退删除正在输入的部分
            for _ in range(len(file_prefix)):
                cursor.deletePreviousChar()
            cursor.insertText(completion)
            
        # 如果补全的是目录，自动补个 / 并重新触发补全
        full_path = os.path.join(self.base_dir, path_prefix, completion)
        if os.path.isdir(full_path):
            cursor.insertText("/")
            # 如果 widget 有触发补全的方法，调用它
            if hasattr(text_edit, 'trigger_path_completion'):
                # 延迟一点点触发，确保 / 已插入文本流
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(10, text_edit.trigger_path_completion)
