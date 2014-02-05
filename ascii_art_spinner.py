"""
ascii_art_spinner.py

Abstracts an ASCII art spinner
"""

import sys


WIDTH, HEIGHT = (0, 0)
progress = 0
terget = 100


def getTerminalSize():
    import os
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            import struct
            import os
            cr = struct.unpack(
                'hh',
                fcntl.ioctl(
                    fd,
                    termios.TIOCGWINSZ,
                    '1234'
                )
            )
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])


def clear():
    """
    Move the buffer backward WIDTH spaces
    """
    sys.stdout.write('\b' * WIDTH)
    sys.stdout.write(' ' * WIDTH)
    sys.stdout.write('\b' * WIDTH)


def draw():
    """
    Draw the ascii art
    NOTE: this expects the cursor to be at the beginning
    """
    sys.stdout.write('[')
    blocks = int(progress / target * WIDTH)
    sys.stdout.write('\u2593' * (blocks))
    sys.stdout.write('\u2591' * (WIDTH - 2 - blocks))
    sys.stdout.write(']')
    sys.stdout.flush()


def tick():
    global progress
    progress += 1
    clear()
    draw()


def start(target_):
    global target, WIDTH, HEIGHT
    target = target_
    WIDTH, HEIGHT = getTerminalSize()
    # keeps things looking nice
    WIDTH -= 1
    draw()
