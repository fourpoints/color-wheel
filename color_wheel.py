import colorsys
import operator
from enum import Enum
from types import SimpleNamespace
from functools import partial
from itertools import chain

# color maps, example: {"red": "#FF0000"}
TEXT_COLOR = {}

ESC = chr(27)

# https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
# https://en.wikipedia.org/wiki/ANSI_escape_code
class SelectGraphicRendition(Enum):
    RESET = 0
    BOLD = 1
    FAINT = 2
    ITALIC = 3
    UNDERLINE = 4
    BLINK = 5
    FAST_BLINK = 6
    SWAP = 7
    CONCEAL = 8
    STRIKETHROUGH = 9
    DEFAULT = 10


# Helper functions

def _join(*codes):
    return ';'.join(map(str, codes))


def _tag(code):
    return "".join((ESC, "[", str(code), "m"))


mulmap = partial(map, operator.mul)
divmap = partial(map, operator.truediv)
addmap = partial(map, operator.add)
def identity(*args): return args


HLS_SCALE = (360, 100, 100)
RGB_SCALE = (255, 255, 255)


def _color_converter(scale1, scale2, converter):
    def _converter(color):
        color = divmap(color, scale1)  # normalize
        color = converter(*color)      # convert
        color = mulmap(color, scale2)  # de-normalize
        color = map(int, color)        # to integer
        return list(color)
    return _converter

hls_to_rgb = _color_converter(HLS_SCALE, RGB_SCALE, colorsys.hls_to_rgb)
rgb_to_hls = _color_converter(HLS_SCALE, RGB_SCALE, colorsys.rgb_to_hls)


def string_to_hextuple(string):
    def tup(s, w, n, f):
        return tuple(f*int(s[1+w*i:1+w*(i+1)], 16) for i in range(n))

    w = len(string) - 1
    if w == 3:  # RGB
        return tup(string, 1, 3, 16)
    elif w == 6:  # RRGGBB
        return tup(string, 2, 3, 1)
    else:
        raise ValueError


# Text effects

class Effect(str):
    @classmethod
    def from_code(cls, code):
        return cls(_tag(code))

    def __mul__(self, other):
        return type(self)(_join(self[:-1], other[2:]))

    def __call__(self, string):
        return "".join((self, string, fx.reset))


class EffectFactory:
    def __init__(self, prefix):
        self.prefix = prefix

    def _effect(self, code):
        return Effect.from_code(_join(self.prefix, *code))

    def __call__(self, color):
        # Infer color format
        if isinstance(color, str):
            return self.css(color)
        elif isinstance(color, tuple):
            return self.rgb(color)
        elif isinstance(color, int):
            return self.hex(color)
        else:
            raise TypeError(f"Color '{color}' of type '{type(color)}' is not supported.")

    # Alias self("red") with self.red
    __getattr__ = __call__

    def css(self, color):
        return self._effect(string_to_hextuple(TEXT_COLOR.get(color, color)))

    def hex(self, color):
        return self.rgb(string_to_hextuple("#" + hex(color)[2:].zfill(6)))

    def rgb(self, color):
        return self._effect(color)

    def hls(self, color):
        return self.rgb(hls_to_rgb(color))


fg = EffectFactory("38;2")
bg = EffectFactory("48;2")
fx = SimpleNamespace(**{e.name.lower(): Effect.from_code(e.value)
    for e in SelectGraphicRendition})


# Gradient wheel

class WheelFactory:
    def __init__(self, from_rgb, to_rgb):
        self.from_rgb = from_rgb
        self.to_rgb = to_rgb

    @staticmethod
    def _parse(effect):
        return map(int, effect[2:-1].split(";"))

    def __getitem__(self, key):
        t0, _2, *rgb0 = self._parse(key.start)
        t1, _2, *rgb1 = self._parse(key.stop)
        if t0 != t1:
            raise TypeError

        return WheelInterpolator(
            t0, self.from_rgb(*rgb0), self.from_rgb(*rgb1), self.to_rgb)


class WheelInterpolator:
    def __init__(self, t, start, end, to_rgb):
        self.t = t
        self.start = start
        self.end = end
        self.to_rgb = to_rgb

    def __call__(self, scalar):
        interpolate = lambda x, y: int(scalar*y + (1-scalar)*x)
        code = _join(self.t, "2", *map(interpolate, self.start, self.end))
        return Effect.from_code(code)

    def gradient(self, string):
        m = 1/(len(string)-1)
        return "".join(chain.from_iterable(
            (self(i*m), c) for i, c in enumerate(string))) + fx.reset


class Wheel:
    rgb = WheelFactory(identity, identity)
    hls = WheelFactory(rgb_to_hls, hls_to_rgb)
