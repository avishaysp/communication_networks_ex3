import sys
import tty
import termios

def _flush_input():
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import sys, termios
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)

def get_single_char():
    """Reads a single character from standard input."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return char

def get_pressed_keys(keys_filter = None):
    """
    
    Returns a list of all pressed keys at the time of the call.

    Parameters:

    keys_filter (list[str]): A list of specific keys to check. If omitted, every key is checked.

    Returns:

    list[str]: A list of currently pressed keys.

    """
    ch = get_single_char()
    if keys_filter:
        return [ch] if ch in keys_filter else []
    return [ch]

def clear_print(*args, **kwargs):
    """

    Clears the terminal before calling print()

    """
    print("\033[H\033[J", end="")
    print(*args, **kwargs)
