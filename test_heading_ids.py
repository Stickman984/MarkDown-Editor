import markdown

md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc', 'fenced_code', 'tables', 'nl2br'])

test_md = """
# 第一个标题

这是第一段内容。

## 第二个标题

这是第二段内容。

### 第三个标题

这是第三段内容。
"""

html = md.convert(test_md)
print("=" * 60)
print("Generated HTML:")
print("=" * 60)
print(html)
print("=" * 60)
print("\nTOC:", md.toc)
