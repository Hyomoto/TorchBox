# API: canvas
---

Imports the canvas module and exposes its methods.  It's important to note that canvas.render() returns
a Sprite object, so it must be converted to a string using concat() to be displayed properly.  This allows
you to use the canvas to draw sprites and compose them into the final canvas if desired.

### Example:
```
import canvas
set CANVAS to canvas.create(80, 24)
canvas.write(CANVAS, "Hello, World!", {"x": 10, "y": 5})
set OUTPUT to concat(canvas.render(CANVAS))
```

## `bar(canvas, x, y, width, progress, **kwargs)`
Draw a progress bar on the canvas.  The pattern can also be a multiple character string where the bar
is drawn gradiated from the first character to the last.

**Parameters:**
- `canvas`: *Canvas*
- `x`: *int*
- `y`: *int*
- `width`: *int*
- `progress`: *float*

**Kwargs:**
- `color`: *None* (default: None)
- `pattern`: *str* (default: '█')
- `split`: *str* (default: None)
- `vertical`: *bool* (default: False)

**Returns:** _None_
## `box(canvas, x, y, width, height, **kwargs)`
Draw a box on the canvas at the specified position with the given width and height.  The pattern can
also be a multiple character string.  If three are provided, the first will be the corners, the second
will be the horizontal edges, and the third will be the vertical edges.  If six are provided, the the
order is top-left, horizontal, top-right, vertical, bottom-right, bottom-left.  Lastly, if outline is False,
one extra character is required and will be used for the fill.

**Parameters:**
- `canvas`: *Canvas*
- `x`: *int*
- `y`: *int*
- `width`: *int*
- `height`: *int*

**Kwargs:**
- `outline`: *bool* (default: True)
- `color`: *str* (default: None)
- `pattern`: *str* (default: '#')

**Returns:** _None_
## `clear(canvas, char)`
Clear the canvas with the specified character.

**Parameters:**
- `canvas`: *Canvas*
- `char`: *str* (default: ' ')

**Returns:** _None_
## `create()`
Returns a canvas with the specified width and height, which is passed to other canvas methods for drawing.

**Returns:** *Canvas: A new canvas object with the specified dimensions.*

## `draw(canvas, sprite, **kwargs)`
Draw a sprite on the canvas at the current position.

**Parameters:**
- `canvas`: *Canvas*
- `sprite`: *Sprite*

**Kwargs:**
- `x`: *int* (default: None, uses current position)
- `y`: *int* (default: None, uses current position)
- `color`: *None* (default: None)

**Returns:** _None_
## `line(canvas, x1, y1, x2, y2, **kwargs)`
Draw a line on the canvas from (x1, y1) to (x2, y2).  The pattern can also be a list of characters,
where the first will be the start, the last will be the end, and the rest will be repeated in between.

**Parameters:**
- `canvas`: *Canvas*
- `x1`: *int*
- `y1`: *int*
- `x2`: *int*
- `y2`: *int*

**Kwargs:**
- `color`: *None* (default: None)
- `pattern`: *str* (default: '*')

**Returns:** _None_
## `linea(canvas, x, y, length, **kwargs)`
Draw a line on the canvas at the current position with a specified length.

**Parameters:**
- `canvas`: *Canvas*
- `x`: *int*
- `y`: *int*
- `length`: *int*

**Kwargs:**
- `color`: *None* (default: None)
- `pattern`: *str* (default: '*')
- `vertical`: *bool* (default: False)

**Returns:** _None_
## `render(canvas)`
Render the canvas to a string representation.

**Parameters:**
- `canvas`: *Canvas*

**Returns:** *Sprite: The rendered canvas as a Sprite object.*

## `write(canvas, text, **kwargs)`
Write text to the canvas at the current canvas position.

**Parameters:**
- `canvas`: *Canvas*
- `text`: *str*

**Kwargs:**
- `color`: *None* (default: None)
- `x`: *int* (default: None, uses current position)
- `y`: *int* (default: None, uses current position)
- `align`: *str* (default: 'left')

**Returns:** _None_

---
