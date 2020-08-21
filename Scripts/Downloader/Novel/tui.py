import curses
import time
from curses.textpad import Textbox, rectangle
from enum import Enum


class Color(Enum):
    WHITE = 1
    PROGRESS_GREEN = 2
    PROGRESS_GREEN_TEXT = 3


def init_colors():
    # (identifier, foreground, background)
    curses.init_pair(Color.WHITE.value, curses.COLOR_RED, curses.COLOR_GREEN)
    curses.init_pair(Color.PROGRESS_GREEN.value, curses.COLOR_GREEN, curses.COLOR_GREEN)
    curses.init_pair(Color.PROGRESS_GREEN_TEXT.value, curses.COLOR_WHITE, curses.COLOR_GREEN)


def create_url_input(screen):
    y, x = screen.getmaxyx()
    uly, ulx = 2, 6
    lines, cols = 1, x - 7
    print(x)

    screen.attron(curses.color_pair(Color.WHITE.value))
    rectangle(screen, 1, 0, 3, 4)
    screen.addstr(2, 1, 'URL')
    win = curses.newwin(lines, cols, uly, ulx)  # lines, columns, y, x
    rectangle(screen, uly - 1, ulx - 1, lines + 2, cols + ulx)  # y, x, lines_from_x, columns_from_x
    url_input = Textbox(win)
    screen.attroff(curses.color_pair(Color.WHITE.value))

    screen.refresh()

    contents = url_input.edit()

    print(contents)


def log(screen, y, x, title, msg=None):
    screen.addstr(y, x, f'[{title}] {msg if msg is not None else ""}')


def progress_bar(screen, progress, uly, ulx, size=0.50):
    max_y, max_x = screen.getmaxyx()

    max_right_bound = int(max_x * size)
    size = 0.99 if size >= 1 else size
    ulx = max_right_bound - 1 if ulx >= max_right_bound else ulx

    pcols = int(max_x * size)
    progress_end_col = (pcols + (ulx + 1)) if (pcols + (ulx + 1)) <= max_x - 1 else max_x - 1
    value = 100 if progress >= 100 else progress
    value = f'{value}%'
    progress = 100 if progress >= 100 else progress
    progress_filled_cols = int(pcols * (progress / 100))  # todo create better formula
    progress_half_cols = int((int(((progress_filled_cols + 1) / 2) - int(len(value) / 2)) + 1) + ulx)
    # progress_half_cols = int(max_x / 2) if progress_half_cols >= max_x - 6 else progress_half_cols

    screen.addstr(uly, ulx, '[')

    # log(screen, max_y - 2, 0, 'VARIABLES')
    log(screen, max_y - 3, 0, 'MAX X', max_x)
    log(screen, max_y - 4, 0, 'MAX Y', max_y)
    log(screen, max_y - 5, 0, 'BOUND X', max_right_bound)
    log(screen, max_y - 6, 0, 'ULX', ulx)
    log(screen, max_y - 7, 0, 'SIZE', size)
    log(screen, max_y - 8, 0, 'PCOL', pcols)
    log(screen, max_y - 9, 0, 'VALUE', value)
    log(screen, max_y - 10, 0, 'PROGRESS FILLED COLS', progress_filled_cols)
    log(screen, max_y - 11, 0, 'PROGRESS END COL', progress_end_col)
    log(screen, max_y - 12, 0, 'PROGRESS HALF COLS', progress_half_cols)

    screen.attron(curses.color_pair(Color.PROGRESS_GREEN.value))
    screen.addstr(uly, ulx + 1, ' ' * progress_filled_cols)
    screen.attroff(curses.color_pair(Color.PROGRESS_GREEN.value))

    screen.attron(curses.color_pair(Color.PROGRESS_GREEN_TEXT.value))
    screen.addstr(uly, progress_half_cols, value)
    screen.attroff(curses.color_pair(Color.PROGRESS_GREEN_TEXT.value))

    screen.addstr(uly, progress_end_col, ']')
    screen.refresh()


def main(main_screen):
    try:
        init_colors()
        y, x = main_screen.getmaxyx()

        main_screen.addstr(0, 0, "Enter IM message: (hit Ctrl-G to send)")

        create_url_input(main_screen)

        progress_bar(main_screen, 100, 4, 200, 0.99)

        # for i in range(1, 200):
        #     main_screen.clear()
        #     progress_bar(main_screen, i, 4, i, i / 100)
        #
        #     time.sleep(0.01)

        main_screen.refresh()
    except Exception as ex:
        print(ex.with_traceback(ex.__traceback__))
    finally:
        main_screen.getkey()


if __name__ == '__main__':
    curses.wrapper(main)
