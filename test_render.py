import tkinter as tk
from tkinterweb import HtmlFrame

root = tk.Tk()
root.geometry("800x600")
root.title("tkinterweb CSS Test")

html_content = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: Arial; padding: 20px; }
    h1 { color: #333; }
    
    /* Code block styling test */
    pre {
        background-color: #282c34;
        color: #abb2bf;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #444;
        font-family: Consolas, monospace;
    }
    code {
        font-family: Consolas, monospace;
    }
    .keyword { color: #c678dd; }
    .string { color: #98c379; }
    .function { color: #61afef; }
</style>
</head>
<body>
    <h1>Code Block Styling Test</h1>
    <p>Below should be a dark code block:</p>
    
    <pre><code><span class="keyword">def</span> <span class="function">hello_world</span>():
    <span class="keyword">print</span>(<span class="string">"Hello, tkinterweb!"</span>)
    <span class="keyword">return</span> <span class="keyword">True</span></code></pre>
    
    <p>End of test.</p>
</body>
</html>
"""

frame = HtmlFrame(root)
frame.load_html(html_content)
frame.pack(fill="both", expand=True)

root.mainloop()
