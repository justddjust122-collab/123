# Datei: pi_explorer_gui.py
# Raspberry Pi Explorer mit:
# - Kopieren + Einfügen
# - Verschieben
# - USB Support
# - Suche
# - Datei Editor
# - Ausführen
# - Blauem GUI

import curses
import os
import shutil
import subprocess

current_path = os.path.expanduser("~")
selected = 0
scroll_offset = 0

clipboard = None
clipboard_mode = None


def get_files(path, search=""):

    try:
        files = os.listdir(path)
        files.sort()

        if search:
            files = [
                f for f in files
                if search.lower() in f.lower()
            ]

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
        input_box(stdscr, "Kein USB gefunden.")
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


def draw_ui(stdscr, files, search):

    global selected
    global scroll_offset
    global clipboard
    global clipboard_mode

    stdscr.clear()

    h, w = stdscr.getmaxyx()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

    stdscr.bkgd(" ", curses.color_pair(1))

    title = f" Raspberry Pi Explorer | {current_path}"

    stdscr.addstr(
        0,
        0,
        title[:w - 1],
        curses.color_pair(2)
    )

    search_text = f"Suche: {search}"

    stdscr.addstr(1, 0, search_text[:w - 1])

    if clipboard:
        clip_text = f"Zwischenablage: {os.path.basename(clipboard)} ({clipboard_mode})"
        stdscr.addstr(2, 0, clip_text[:w - 1])

    help_lines = [
        "HOCH/RUNTER = Scrollen",
        "ENTER = Öffnen / Menü",
        "BACKSPACE = Zurück",
        "S = Suche",
        "U = USB Auswahl",
        "P = Einfügen",
        "Q = Beenden"
    ]

    for i, line in enumerate(help_lines):

        stdscr.addstr(
            h - len(help_lines) + i - 1,
            0,
            line[:w - 1],
            curses.color_pair(2)
        )

    visible_height = h - 12

    if selected < scroll_offset:
        scroll_offset = selected

    if selected >= scroll_offset + visible_height:
        scroll_offset = selected - visible_height + 1

    for idx in range(
        scroll_offset,
        min(len(files), scroll_offset + visible_height)
    ):

        file = files[idx]

        y = idx - scroll_offset + 4

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


def file_menu(stdscr):

    options = [
        "Ausführen",
        "Editor",
        "Löschen",
        "Kopieren",
        "Verschieben",
        "Umbenennen",
        "Neue Datei",
        "Neuer Ordner",
        "Zurück"
    ]

    choice = 0

    while True:

        stdscr.clear()

        stdscr.addstr(0, 0, "Datei Menü")

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


def paste_file():

    global clipboard
    global clipboard_mode
    global current_path

    if not clipboard:
        return

    name = os.path.basename(clipboard)

    ziel = os.path.join(current_path, name)

    if clipboard_mode == "copy":

        if os.path.isdir(clipboard):
            shutil.copytree(clipboard, ziel)
        else:
            shutil.copy2(clipboard, ziel)

    elif clipboard_mode == "move":

        shutil.move(clipboard, ziel)

        clipboard = None
        clipboard_mode = None


def main(stdscr):

    global current_path
    global selected
    global clipboard
    global clipboard_mode

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

            search = input_box(
                stdscr,
                "Suche:"
            )

            selected = 0

        elif key == ord("u"):

            usb = choose_usb(stdscr)

            if usb:
                current_path = usb
                selected = 0

        elif key == ord("p"):

            try:
                paste_file()

            except Exception as e:
                input_box(stdscr, f"Fehler: {e}")

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

                action = file_menu(stdscr)

                try:

                    if action == "Ausführen":

                        cmd = input_box(
                            stdscr,
                            "Befehl:"
                        )

                        curses.endwin()

                        subprocess.run(
                            cmd.split() + [full_path]
                        )

                        input("ENTER drücken...")

                    elif action == "Editor":

                        curses.endwin()

                        subprocess.run(
                            ["nano", full_path]
                        )

                    elif action == "Löschen":

                        os.remove(full_path)

                    elif action == "Kopieren":

                        clipboard = full_path
                        clipboard_mode = "copy"

                    elif action == "Verschieben":

                        clipboard = full_path
                        clipboard_mode = "move"

                    elif action == "Umbenennen":

                        neu = input_box(
                            stdscr,
                            "Neuer Name:"
                        )

                        os.rename(
                            full_path,
                            os.path.join(
                                current_path,
                                neu
                            )
                        )

                    elif action == "Neue Datei":

                        name = input_box(
                            stdscr,
                            "Dateiname:"
                        )

                        open(
                            os.path.join(
                                current_path,
                                name
                            ),
                            "w"
                        ).close()

                    elif action == "Neuer Ordner":

                        name = input_box(
                            stdscr,
                            "Ordnername:"
                        )

                        os.mkdir(
                            os.path.join(
                                current_path,
                                name
                            )
                        )

                except Exception as e:

                    input_box(
                        stdscr,
                        f"Fehler: {e}"
                    )

    curses.endwin()


if __name__ == "__main__":
    curses.wrapper(main)
