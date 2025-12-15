# 详细测试：缩进对方括号显示的影响

## 测试组1：纯文本（不在代码块中）

### 无缩进
[ro.lmk.swap_free_low_percentage]: [15]

### 2个空格
  [ro.lmk.swap_free_low_percentage]: [15]

### 4个空格
    [ro.lmk.swap_free_low_percentage]: [15]

---

## 测试组2：代码块

### 情况A：代码块无缩进
```
[ro.lmk.swap_free_low_percentage]: [15]
```

### 情况B：代码块2个空格缩进
  ```
  [ro.lmk.swap_free_low_percentage]: [15]
  ```

### 情况C：代码块4个空格缩进
    ```
    [ro.lmk.swap_free_low_percentage]: [15]
    ```

### 情况D：代码块1个空格缩进
 ```
 [ro.lmk.swap_free_low_percentage]: [15]
 ```

### 情况E：代码块3个空格缩进
   ```
   [ro.lmk.swap_free_low_percentage]: [15]
   ```

---

## 测试组3：列表中的代码块

- 无额外空行
  ```
  [ro.lmk.swap_free_low_percentage]: [15]
  ```

- 有空行
  
  ```
  [ro.lmk.swap_free_low_percentage]: [15]
  ```

---

## 测试组4：引用块中

> 引用中的代码块：
> ```
> [ro.lmk.swap_free_low_percentage]: [15]
> ```

---

## 请记录哪些能显示，哪些不能

请在预览中查看，然后告诉我：
- 测试组1：哪些显示？
- 测试组2：A-E哪些显示？
- 测试组3：哪个显示？
- 测试组4：是否显示？
