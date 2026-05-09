# Datei: pi_explorer_gui.py
# Raspberry Pi Datei Explorer mit GUI + Suche + USB Auswahl

import curses
import os
import shutil
import subprocess

current_path = os.path.expanduser("~")
selected = 0
scroll_offset = 0


def get_files(path, search=""):
    try:
        files = os.listdir(path)
        files.sort()

        if search:
            files = [f for f in files if search.lower() in f.lower()]

        return [".."] + files
    except:
        return [".."]


def find_usb():
    usb_list = []

    paths = [
        "/media/pi",
        f"/media/{os.getenv('USER')}",
        "/mnt"
    ]

    for base in paths:
        if os.path.exists(base):
            try:
                for item in os.listdir(base):
                    full = os.path.join(base, item)

                    if os.path.ismount(full):
                        usb_list.append(full)
            except:
                pass

    return usb_list


def draw_ui(stdscr, files, search):
    global selected, scroll_offset

    stdscr.clear()

    h, w = stdscr.getmaxyx()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

    stdscr.bkgd(" ", curses.color_pair(1))

    title = f" Raspberry Pi Explorer | {current_path}"
    stdscr.addstr(0, 0, title[:w - 1], curses.color_pair(2))

    search_text = f"Suche: {search}"
    stdscr.addstr(1, 0, search_text[:w - 1])

    help_lines = [
        "HOCH/RUNTER = Scrollen",
        "ENTER = Öffnen / Menü",
        "BACKSPACE = Zurück",
        "S = Suche",
        "U = USB Auswahl",
        "Q = Beenden"
    ]

    for i, line in enumerate(help_lines):
        stdscr.addstr(
            h - len(help_lines) + i - 1,
            0,
            line[:w - 1],
            curses.color_pair(2)
        )

    visible_height = h - 10

    if selected < scroll_offset:
        scroll_offset = selected

    if selected >= scroll_offset + visible_height:
        scroll_offset = selected - visible_height + 1

    for idx in range(
        scroll_offset,
        min(len(files), scroll_offset + visible_height)
    ):

        file = files[idx]

        y = idx - scroll_offset + 3

        full = os.path.join(current_path, file)

        if os.path.isdir(full):
            display = f"[ORDNER] {file}"
        else:
            display = f"         {file}"

        if idx == selected:
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(y, 0, display[:w - 1])
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(y, 0, display[:w - 1])

    stdscr.refresh()


def input_box(stdscr, text):
    curses.echo()

    stdscr.clear()

    stdscr.addstr(0, 0, text)

    stdscr.refresh()

    value = stdscr.getstr(2, 0).decode("utf-8")

    curses.noecho()

    return value


def choose_usb(stdscr):
    usbs = find_usb()

    if not usbs:
        input_box(stdscr, "Kein USB gefunden. ENTER drücken.")
        return None

    choice = 0

    while True:
        stdscr.clear()

        stdscr.addstr(0, 0, "USB Stick auswählen")

        for i, usb in enumerate(usbs):

            if i == choice:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(i + 2, 0, usb)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 0, usb)

        key = stdscr.getch()

        if key == curses.KEY_UP:
            choice = (choice - 1) % len(usbs)

        elif key == curses.KEY_DOWN:
            choice = (choice + 1) % len(usbs)

        elif key == 10:
            return usbs[choice]

        elif key == 27:
            return None


def file_menu(stdscr, full_path):
    options = [
        "Ausführen",
        "Editor",
        "Löschen",
        "Verschieben",
        "Kopieren",
        "Umbenennen",
        "Auf USB kopieren",
        "Neue Datei",
        "Neuer Ordner",
        "Zurück"
    ]

    choice = 0

    while True:
        stdscr.clear()

        stdscr.addstr(0, 0, full_path)

        for i, opt in enumerate(options):

            if i == choice:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(i + 2, 0, opt)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 0, opt)

        key = stdscr.getch()

        if key == curses.KEY_UP:
            choice = (choice - 1) % len(options)

        elif key == curses.KEY_DOWN:
            choice = (choice + 1) % len(options)

        elif key == 10:
            return options[choice]


def main(stdscr):
    global current_path
    global selected

    curses.curs_set(0)

    stdscr.keypad(True)

    search = ""

    while True:

        files = get_files(current_path, search)

        if selected >= len(files):
            selected = len(files) - 1

        draw_ui(stdscr, files, search)

        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected = max(0, selected - 1)

        elif key == curses.KEY_DOWN:
            selected = min(len(files) - 1, selected + 1)

        elif key == ord("q"):
            break

        elif key == ord("s"):
            search = input_box(stdscr, "Suche eingeben:")
            selected = 0

        elif key == ord("u"):
            usb = choose_usb(stdscr)

            if usb:
                current_path = usb
                selected = 0

        elif key == curses.KEY_BACKSPACE or key == 127:
            current_path = os.path.dirname(current_path)
            selected = 0

        elif key == 10:

            file = files[selected]

            full_path = os.path.join(current_path, file)

            if os.path.isdir(full_path):
                current_path = os.path.abspath(full_path)
                selected = 0

            else:

                action = file_menu(stdscr, full_path)

                try:

                    if action == "Ausführen":

                        cmd = input_box(
                            stdscr,
                            "Befehl eingeben (z.B python3):"
                        )

                        curses.endwin()

                        subprocess.run(cmd.split() + [full_path])

                        input("ENTER drücken...")

                    elif action == "Editor":
                        curses.endwin()
                        subprocess.run(["nano", full_path])

                    elif action == "Löschen":
                        os.remove(full_path)

                    elif action == "Verschieben":

                        ziel = input_box(stdscr, "Zielordner:")

                        shutil.move(full_path, ziel)

                    elif action == "Kopieren":

                        ziel = input_box(stdscr, "Zielordner:")

                        shutil.copy(full_path, ziel)

                    elif action == "Umbenennen":

                        neu = input_box(stdscr, "Neuer Name:")

                        os.rename(
                            full_path,
                            os.path.join(current_path, neu)
                        )

                    elif action == "Auf USB kopieren":

                        usb = choose_usb(stdscr)

                        if usb:
                            shutil.copy(full_path, usb)

                    elif action == "Neue Datei":

                        name = input_box(stdscr, "Dateiname:")

                        open(
                            os.path.join(current_path, name),
                            "w"
                        ).close()

                    elif action == "Neuer Ordner":

                        name = input_box(stdscr, "Ordnername:")

                        os.mkdir(
                            os.path.join(current_path, name)
                        )

                except Exception as e:
                    input_box(stdscr, f"Fehler: {e}")

    curses.endwin()


if __name__ == "__main__":
    curses.wrapper(main)
