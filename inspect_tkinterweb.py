import tkinter as tk
from tkinterweb import HtmlFrame
import time

root = tk.Tk()
frame = HtmlFrame(root)
frame.pack(fill="both", expand=True)

frame.load_html("<h1>Test</h1><p>Content</p>")
root.update()

print("Attributes of HtmlFrame:")
for attr in dir(frame):
    if not attr.startswith("_"):
        print(attr)

print("\nAttributes of frame.html (if exists):")
if hasattr(frame, 'html'):
    for attr in dir(frame.html):
        if not attr.startswith("_"):
            print(attr)

print("\nChildren of HtmlFrame:")
for child in frame.winfo_children():
    print(f"Child: {child}, Class: {child.winfo_class()}")
    for attr in dir(child):
        if 'yview' in attr or 'scroll' in attr:
            print(f"  Has {attr}")

root.destroy()
