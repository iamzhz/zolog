---
date: 2026-1-2
description: 利用泰勒展开实现了简单的 sin(x) 函数, 并讨论了正规标准库是如何实现 sin(x) 的
tags: math
tags: code
tags: glibc
---
# 怎么用代码实现正弦值计算
---
## 泰勒展开
根据泰勒展开, 我们都知道: 
<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mi>sin</mi><mo data-mjx-texclass="NONE">⁡</mo><mi>x</mi><mo>=</mo><mi>x</mi><mo>−</mo><mfrac><msup><mi>x</mi><mrow><mn>3</mn></mrow></msup><mrow><mn>3</mn><mo>!</mo></mrow></mfrac><mo>+</mo><mfrac><msup><mi>x</mi><mrow><mn>5</mn></mrow></msup><mrow><mn>5</mn><mo>!</mo></mrow></mfrac><mo>−</mo><mfrac><msup><mi>x</mi><mrow><mn>7</mn></mrow></msup><mrow><mn>7</mn><mo>!</mo></mrow></mfrac><mo>+</mo><mo>⋯</mo><mo>+</mo><mfrac><mrow><mo stretchy="false">(</mo><mo>−</mo><mn>1</mn><msup><mo stretchy="false">)</mo><mrow><mi>n</mi></mrow></msup><msup><mi>x</mi><mrow><mn>2</mn><mi>n</mi><mo>+</mo><mn>1</mn></mrow></msup></mrow><mrow><mo stretchy="false">(</mo><mn>2</mn><mi>n</mi><mo>+</mo><mn>1</mn><mo stretchy="false">)</mo><mo>!</mo></mrow></mfrac><mo>+</mo><mo>…</mo></math>
只取前几项的话
<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mi>f</mi><mo stretchy="false">(</mo><mi>x</mi><mo stretchy="false">)</mo><mo>=</mo><mi>x</mi><mo>−</mo><mfrac><msup><mi>x</mi><mrow><mn>3</mn></mrow></msup><mn>6</mn></mfrac><mo>+</mo><mfrac><msup><mi>x</mi><mrow><mn>5</mn></mrow></msup><mn>120</mn></mfrac></math>
发现 f(x) 从 [0, π/2] 的值和 sin(x) 的值差的[也不是很多](https://www.desmos.com/calculator/7lowczhumd)嘛~(我的要求没那么高):  
<iframe src="https://www.desmos.com/calculator/7lowczhumd?embed" width="250" height="250" style="border: 1px solid #ccc" frameborder=0></iframe>  
就很好办辣~

### Coding
先来第一步取模, 把自变量的取值缩小到 [0, 2π), 再缩到 [0, π], 接着是 [0, π/2]. 现在就可以用 f(x) 计算近似的正弦值啦.  
```c
/* my sin(x) */
#define myPI 3.1415926
// 这个实现后文我会称作"咱的 f(x)"
double f(double x) {
    // to [0, 2π)
    double twopi = 2.0 * myPI;
    x = fmod(x, twopi);
    if (x < 0) x += twopi;
    
    // to [0, π/2]
    int sign = 1;
    if (x >= myPI) {
        x -= myPI;
        sign = -1;
    }
    if (x > 0.5 * myPI) {
        x = myPI - x;
    }
    // now x is all in [-π/2, π/2]
    double x2 = x * x; // x^2
    double x3 = x2 * x; // x^3
    double x5 = x2 * x3; // x^5
    return sign * (x-x3/6+x5/120);
}
```
我测试了一下, 精度还是能用的, 当 `x=π/2` 时, 有 f(x)-sin(x) 的最大值≈ `0.00452485553`.  
还行  
## 编程语言实现中的正弦函数具体写法
很多编程语言标准库中都是包含 sin(x) 函数的, 当然, 它肯定不能像咱的 f(x) 写的这么糙, 来瞅眼  
### glibc
> 接下来我会用"输入"这个字眼来代替 sin(x) 的自变量的值.

glibc 中的 sin() 实现可以在[这里](https://elixir.bootlin.com/glibc/glibc-2.42/source/sysdeps/ieee754/dbl-64/s_sin.c)查看, 函数入口是这个文件中的 `__sin()` 函数.   
不得不说还得是 glibc, 它在不同输入范围时, 会同时确保精度和速度, 使用不同的方法计算(当然, 核心还是泰勒展开).  
先介绍一些 __sin() 所调用的函数:  

- `reduce_sincos()`: 范围缩减, 把范围缩到 `-π/4~π/4`. (类似咱的 f(x) 中的 `to [0, 2π)` 和 `to [0, π/2]`)  
- `__branred()`: 同样是范围缩减, 但比 `reduce_sincos()` 更复杂, 更适合大数. 在[这里](https://elixir.bootlin.com/glibc/glibc-2.42/source/sysdeps/ieee754/dbl-64/branred.c#L53)可以查看它的实现.  
- `do_sin()`, `do_cos()`: 计算的核心, 在输入较小时, 它会直接干脆利落地用泰勒级数(这时误差较小); 而... 当输入大于某个阈值时, 为了缩小误差, 在利用泰勒级数的同时会查表来补偿误差(没错, 就是查表, 查 [400 行的表](https://elixir.bootlin.com/glibc/glibc-2.42/source/sysdeps/ieee754/dbl-64/sincostab.c#L28)).  
- `do_sincos()`: 我们知道, 泰勒级数计算总归有点误差, 而当输入更接近原点的误差更小, 这个函数会在判断后有选择地使用 do_sin() 或 do_cos() 来计算.  
---
下面正式介绍一下 `__sin()`, 它所做的主要是`判范围, 选方法, 去用`:  
> 我们下面所说的"大小"指输入的绝对值大小

- 当输入极小时, 函数图像与 `y=x` 极接近, 直接用输入值代替返回值.  
- 再大些时, 范围还是比较小, 可以直接用 `do_sin()`.  
- 再大些时, 范围相对小, 用 `do_cos()`.  
- 再大些时, 范围大了, 需要 `reduce_sincos()` 去缩, 再调用 `do_sincos()`.  
- 再大些时, 范围很大啦, 直接使用 `reduce_sincos()` 会产生误差, 所以这里会使用 `__branred()` 来缩范围(开销更大也更精确), 再调用 `do_sincos()`.  
- 再大些时, 这时已经极大了, 还算什么算啊, 返回 `NaN` 得了.  
### CPython
给 C 语言的 sin() 函数套了个壳, 包括其他很多数学函数也是这样干的  
(最初我还以为它会自己实现一个呢, 不过我很理解)  
可以到[这里](https://github.com/python/cpython/blob/864c5985ea986db873ded40f09d7269bfe39df98/Modules/mathmodule.c#L1154C5-L1154C6)来看, 直接套了宏

## 参见
- [My Useless Contribution to the GNU C Sine Function](https://www.awelm.com/posts/sine)
- [Range reduction in glibc with reduce_sincos](https://www.homepages.ucl.ac.uk/~ucahmto/programming/2024/09/16/reduce-sincos-range-reduction.html)