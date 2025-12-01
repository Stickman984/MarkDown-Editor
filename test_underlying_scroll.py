import tkinter as tk
from tkinterweb import HtmlFrame
import time

root = tk.Tk()
root.geometry("800x600")

frame = HtmlFrame(root)
frame.pack(fill="both", expand=True)

# Load long content
long_html = "<html><body>" + "<br>".join([f"Line {i}" for i in range(100)]) + "</body></html>"
frame.load_html(long_html)
root.update()

# Scroll down
print("Scrolling down...")
if hasattr(frame, 'html'):
    frame.html.yview_moveto(0.5)
    root.update()
    
    # Check yview
    yview = frame.html.yview()
    print(f"frame.html.yview(): {yview}")
    
    if yview and yview != (0.0, 1.0):
        print("SUCCESS: Got valid scroll position from underlying widget!")
    else:
        print("FAILURE: yview returned None or default")
else:
    print("FAILURE: frame.html does not exist")

root.destroy()
