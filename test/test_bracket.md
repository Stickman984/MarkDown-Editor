# 测试方括号语法

## 问题例子（不显示）

这种格式会被误认为是链接引用定义，所以不显示：
[ro.lmk.swap_free_low_percentage]: [15]

## 解决方案1：使用代码格式

行内代码：`[ro.lmk.swap_free_low_percentage]: [15]`

代码块：
```
[ro.lmk.swap_free_low_percentage]: [15]
```

    ```
    [ro.lmk.swap_free_low_percentage]: [15]
    ```

## 解决方案2：使用转义字符

\[ro.lmk.swap_free_low_percentage\]: \[15\]

## 解决方案3：使用HTML实体

&#91;ro.lmk.swap_free_low_percentage&#93;: &#91;15&#93;

## 解决方案4：使用表格

| 属性 | 值 |
|------|-----|
| `ro.lmk.swap_free_low_percentage` | `15` |

