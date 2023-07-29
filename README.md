# color-wheel
Python ANSI coloring module for terminal

## Example usage

```python
from color_wheel import fx, fg, bg, Wheel

# Concatenation
fmt = fx.strikethrough * fg.red * bg.hls((244, 30, 30))
print(fmt + "hello world" + fx.reset)

# Call warp
fmt = fx.bold * fg("green")
print(fmt("hello world"))

# Gradient
wheel = Wheel.rgb[bg.green:bg.gray]
print(wheel(0.5)("hello world"))
print(wheel.gradient("hello world"))

# Hex code
print(fg.hex(0xc0ffee)("hello world"))
```

Combine `Effect` object (subclass of `str`) using the `*` operator.
