import tkinter as tk
from tkinterweb import HtmlFrame

root = tk.Tk()
root.geometry("800x600")

frame = HtmlFrame(root, messages_enabled=False)
frame.pack(fill="both", expand=True)

# 加载一个长文档
long_html = """
<html>
<body>
<h1>Test Scroll Position</h1>
""" + "\n".join([f"<p>Line {i}: This is a test paragraph to create a scrollable document.</p>" for i in range(100)]) + """
</body>
</html>
"""

frame.load_html(long_html)

def test_scroll_api():
    print("Testing scroll API...")
    print(f"dir(frame): {[attr for attr in dir(frame) if 'scroll' in attr.lower() or 'yview' in attr.lower()]}")
    
    # 尝试获取 yview
    try:
        if hasattr(frame, 'yview'):
            yview = frame.yview()
            print(f"frame.yview(): {yview}")
    except Exception as e:
        print(f"frame.yview() error: {e}")
    
    # 尝试访问内部组件
    try:
        children = frame.winfo_children()
        print(f"Children: {children}")
        for child in children:
            print(f"  Child: {child}, has yview: {hasattr(child, 'yview')}")
            if hasattr(child, 'yview'):
                try:
                    yview = child.yview()
                    print(f"  {child}.yview(): {yview}")
                except Exception as e:
                    print(f"  {child}.yview() error: {e}")
    except Exception as e:
        print(f"winfo_children error: {e}")

tk.Button(root, text="Test Scroll API", command=test_scroll_api, font=("Arial", 16)).place(x=10, y=10)

root.mainloop()
