# 代码块测试
这种可以
```c
void *erofs_get_pcpubuf(unsigned int requiredpages)
  	__acquires(pcb->lock)
  {
  	struct erofs_pcpubuf *pcb = &get_cpu_var(erofs_pcb);
  
  	raw_spin_lock(&pcb->lock);
  	/* check if the per-CPU buffer is too small */
  	if (requiredpages > pcb->nrpages) {
  		raw_spin_unlock(&pcb->lock);
  		put_cpu_var(erofs_pcb);
  		/* (for sparse checker) pretend pcb->lock is still taken */
  		__acquire(pcb->lock);
  		return NULL;
  	}
  	return pcb->ptr;
  }
```

- 不能显示代码块，下面内容全是纯文本，包括```c    ```这个代码块标记
    ```c
    void *erofs_get_pcpubuf(unsigned int requiredpages)
      	__acquires(pcb->lock)
      {
      	struct erofs_pcpubuf *pcb = &get_cpu_var(erofs_pcb);
  
  	raw_spin_lock(&pcb->lock);
    	/* check if the per-CPU buffer is too small */
    	if (requiredpages > pcb->nrpages) {
  	 	raw_spin_unlock(&pcb->lock);
    		put_cpu_var(erofs_pcb);
     		/* (for sparse checker) pretend pcb->lock is still taken */
      		__acquire(pcb->lock);
      		return NULL;
      	}
      	return pcb->ptr;
      }
    ```


代码块不能识别C语言，```c    ```也成了代码块的一部分

    ```c
    void *erofs_get_pcpubuf(unsigned int requiredpages)
      	__acquires(pcb->lock)
      {
      	struct erofs_pcpubuf *pcb = &get_cpu_var(erofs_pcb);
  
  	raw_spin_lock(&pcb->lock);
    	/* check if the per-CPU buffer is too small */
    	if (requiredpages > pcb->nrpages) {
  	 	raw_spin_unlock(&pcb->lock);
    		put_cpu_var(erofs_pcb);
     		/* (for sparse checker) pretend pcb->lock is still taken */
      		__acquire(pcb->lock);
      		return NULL;
      	}
      	return pcb->ptr;
      }
    ```

代码块不能识别C语言，```c    ```也成了代码块的一部分
    ```c
    void *erofs_get_pcpubuf(unsigned int requiredpages)
      	__acquires(pcb->lock)
      {
      	struct erofs_pcpubuf *pcb = &get_cpu_var(erofs_pcb);
        raw_spin_lock(&pcb->lock);
    	/* check if the per-CPU buffer is too small */
    	if (requiredpages > pcb->nrpages) {
  	 	raw_spin_unlock(&pcb->lock);
    		put_cpu_var(erofs_pcb);
     		/* (for sparse checker) pretend pcb->lock is still taken */
      		__acquire(pcb->lock);
      		return NULL;
      	}
      	return pcb->ptr;
      }
    ```

代码块不能识别C语言，```c    ```也成了代码块的一部分
    ```c
    void *erofs_get_pcpubuf(unsigned int requiredpages)
      	__acquires(pcb->lock)
      {
        struct erofs_pcpubuf *pcb = &get_cpu_var(erofs_pcb);
        raw_spin_lock(&pcb->lock);
    	/* check if the per-CPU buffer is too small */

    	if (requiredpages > pcb->nrpages) {
            raw_spin_unlock(&pcb->lock);
    		put_cpu_var(erofs_pcb);
     		/* (for sparse checker) pretend pcb->lock is still taken */
      		__acquire(pcb->lock);
      		return NULL;
      	}
      	return pcb->ptr;
      }
    ```