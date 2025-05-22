from canvas import Canvas, Ansi, getColorSpans

def make(string, color = None):
  raw, _ = getColorSpans(string, color)
  width = max(len(line) for line in raw)
  canvas = Canvas(width, len(raw))
  canvas.write(string, color=color)
  return canvas.render()

title = make(
"###  ###   ##   ##   ##  ##  #\n"
f"{Ansi.WHITE}## # ## # ## # ## # ## # ### #{Ansi.RESET}\n"
f"{Ansi.WHITE}## # ## # ## # ##   ## # ### #{Ansi.RESET}\n"
"## # ###  #### #### ## # ## ##\n"
"## # ## # ## # ## # ## # ## ##\n"
"###  ## # ## #  ##   ##  ##  #")

dragons = make(
"    _)               (_\n"
f"   _) \\ /\\{Ansi.PURPLE}%{Ansi.RESET}/\\ /\\_/\\ / (_\n"
f"  _)  \\\\({Ansi.BLUE}0 0{Ansi.RESET}) ({Ansi.RED}0 0{Ansi.RESET})//  (_\n"
"  )_ -- \\(oo) (oo)/ -- _(\n"
"   )_ / /\\\\__,__//\\ \\ _(\n"
"    )_ /   --;--   \\ _(\n"
"*.    ( (  )) ((  ) )    .*\n"
f"  '...(____){Ansi.WHITE}z z{Ansi.RESET}(____)...'")

header = make(
f"                            ▄▄▄▄▄▄▄▄▄▄▄ \n"
f"  ▄▄▓▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ▀▓\n"
f" ░▒▓██████████████████████████████████  \n"
f"  ░▒▓█████████████████████████████████ ░\n"
f"   ░▒▓████████████████████████████████ ▒\n"
f"     ▄  ▄ ▄▄ ▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▓\n"
f"                         ▀              "
)
# ░▒▓█ ▀▄

def _():
    screen = Canvas(40, 18)
    screen.box(0, 0, screen.width, screen.height, color = Ansi.GREEN, outline=True, pattern=("┌","─","┐","│","┘","└"))
    screen.draw(title,  x = (screen.width - title.width)//2, y = 2, color = Ansi.RED)
    screen.draw(dragons,x = (screen.width - dragons.width)//2, y = 8, color = Ansi.YELLOW)
    return screen.render()
dragonscreen = _()
