import re
import markdown

def preprocess(text):
    # Pattern: [key]: [value] (with optional indentation)
    # We escape the first [ to prevent it being parsed as a reference link
    # Regex explanation:
    # ^(\s*)   : Start of line, capture indentation
    # \[       : Literal [
    # ([^\]\n]+) : Capture Group 2: content inside first brackets (key)
    # \]       : Literal ]
    # :        : Literal colon
    # (\s*)    : Capture Group 3: spacing
    # \[       : Literal [ (This implies the value is ALSO bracketed)
    # ([^\]\n]+) : Capture Group 4: content inside second brackets (value)
    # \]       : Literal ]
    pattern = re.compile(r'^(\s*)\[([^\]\n]+)\]:(\s*)\[([^\]\n]+)\]', re.MULTILINE)
    return pattern.sub(r'\1\[\2]:\3[\4]', text)

text = """
### Test Case 1: The user's issue
[ro.lmk.swap_free_low_percentage]: [15]

### Test Case 2: Indented user issue
  [ro.lmk.swap_free_low_percentage]: [15]

### Test Case 3: Normal Reference Link (Should NOT change)
[google]: https://google.com "Google"

### Test Case 4: Reference Link with title
[foo]: /url "title"

### Test Case 5: Bracketed URL (Uncommon but valid markdown? Maybe)
[weird]: [url]
"""

print("--- Original ---")
print(text)
processed = preprocess(text)
print("\n--- Processed ---")
print(processed)

print("\n--- Rendered HTML (Processed) ---")
print(markdown.markdown(processed))
