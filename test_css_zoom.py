import tkinter as tk
from tkinterweb import HtmlFrame

root = tk.Tk()
root.geometry("800x600")

frame = HtmlFrame(root, messages_enabled=False)
frame.pack(fill="both", expand=True)

# 测试各种缩放方法
html_templates = {
    "CSS zoom": """
    <html>
    <head>
        <style>
            body { zoom: 2.0; }
        </style>
    </head>
    <body>
        <h1>Test CSS zoom: 2.0</h1>
        <p>This text should be 2x larger if zoom is supported.</p>
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='red'/%3E%3C/svg%3E" />
    </body>
    </html>
    """,
    
    "CSS transform scale": """
    <html>
    <head>
        <style>
            body { 
                transform: scale(2.0);
                transform-origin: top left;
            }
        </style>
    </head>
    <body>
        <h1>Test CSS transform scale: 2.0</h1>
        <p>This text should be 2x larger if transform is supported.</p>
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='blue'/%3E%3C/svg%3E" />
    </body>
    </html>
    """,
    
    "Font size scaling": """
    <html>
    <head>
        <style>
            body { font-size: 28px; }  /* 2x of 14px */
            img { width: 200px; height: 200px; }  /* 2x of 100px */
        </style>
    </head>
    <body>
        <h1>Test font-size scaling</h1>
        <p>This uses font-size: 28px and explicit image size.</p>
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='green'/%3E%3C/svg%3E" />
    </body>
    </html>
    """
}

current_test = [0]

def next_test():
    keys = list(html_templates.keys())
    current_test[0] = (current_test[0] + 1) % len(keys)
    test_name = keys[current_test[0]]
    print(f"Loading test: {test_name}")
    frame.load_html(html_templates[test_name])

# 初始加载
next_test()

tk.Button(root, text="Next Test", command=next_test, font=("Arial", 16)).place(x=10, y=10)

root.mainloop()
