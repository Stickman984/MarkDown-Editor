import sys
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from table_helper import TableHelperDialog

def test_markdown_spacing():
    app = QApplication(sys.argv)
    dialog = TableHelperDialog()
    
    # 设置 2x2 表格
    dialog.table.setRowCount(2)
    dialog.table.setColumnCount(2)
    
    # 填充数据，包括长 URL
    dialog.table.setItem(0, 0, QTableWidgetItem("Header 1"))
    dialog.table.setItem(0, 1, QTableWidgetItem("Header 2"))
    dialog.table.setItem(1, 0, QTableWidgetItem("Long URL"))
    dialog.table.setItem(1, 1, QTableWidgetItem("https://scgit.amlogic.com/#/c/626035/"))
    
    markdown = dialog.generate_markdown()
    print("Generated Markdown:\n")
    print(markdown)
    
    # 检查是否有过度空格
    # URL 长度为 37，Header 2 长度为 8。
    # 视觉宽度应该是 37。
    # 旧逻辑会填充到 37 * 2 = 74 个字符宽。
    # 新逻辑应该是 37 个字符。
    
    lines = markdown.split('\n')
    url_line = lines[2]
    # | Long URL | https://scgit.amlogic.com/#/c/626035/ |
    # 视觉宽度验证
    content = url_line.split('|')[2].strip()
    full_field = url_line.split('|')[2]
    print(f"\nURL Field length (including padding): {len(full_field)}")
    print(f"URL content length: {len(content)}")
    
    if len(full_field) < 50:
        print("\nTest passed: No excessive spacing detected.")
    else:
        print("\nTest failed: Excessive spacing still present.")
    
    sys.exit(0)

if __name__ == "__main__":
    test_markdown_spacing()
