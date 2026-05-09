# Datei: pi_explorer.py
# Terminal Datei-Explorer für Raspberry Pi
# Steuerung:
# Pfeile Hoch/Runter = Navigieren
# ENTER = Menü öffnen
# BACKSPACE = Zurück zum Ordner davor
# q = Beenden

import curses
import os
import shutil
import subprocess

current_path = os.path.expanduser("~")
selected = 0
scroll_offset = 0


def get_files(path):
    try:
        files = os.listdir(path)
        files.sort()
        return [".."] + files
    except:
        return [".."]


def draw_menu(stdscr, files):
    global selected, scroll_offset

    stdscr.clear()
    h, w = stdscr.getmaxyx()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

    stdscr.bkgd(" ", curses.color_pair(1))

    title = f" Raspberry Pi Explorer | {current_path} "
    stdscr.addstr(0, 0, title[:w - 1], curses.color_pair(2))

    help_text = "Pfeile = Scrollen | ENTER = Menü | BACKSPACE = Zurück | q = Ende"
    stdscr.addstr(h - 1, 0, help_text[:w - 1], curses.color_pair(2))

    visible_height = h - 2

    if selected < scroll_offset:
        scroll_offset = selected

    if selected >= scroll_offset + visible_height:
        scroll_offset = selected - visible_height + 1

    for idx in range(scroll_offset, min(len(files), scroll_offset + visible_height)):
        file = files[idx]
        y = idx - scroll_offset + 1

        full_path = os.path.join(current_path, file)

        if os.path.isdir(full_path):
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


def action_menu(stdscr, file_name):
    options = [
        "Öffnen",
        "Löschen",
        "Verschieben",
        "Kopieren",
        "Neuer Ordner",
        "Neue Datei",
        "Umbenennen",
        "Editor",
        "Ausführen",
        "Auf USB kopieren",
        "Zurück"
    ]

    choice = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Datei: {file_name}")

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


def find_usb():
    usb_paths = ["/media/pi", "/mnt"]

    found = []

    for base in usb_paths:
        if os.path.exists(base):
            for item in os.listdir(base):
                found.append(os.path.join(base, item))

    return found


def main(stdscr):
    global current_path, selected

    curses.curs_set(0)
    stdscr.keypad(True)

    while True:
        files = get_files(current_path)

        if selected >= len(files):
            selected = len(files) - 1

        draw_menu(stdscr, files)

        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected = max(0, selected - 1)

        elif key == curses.KEY_DOWN:
            selected = min(len(files) - 1, selected + 1)

        elif key == curses.KEY_BACKSPACE or key == 127:
            current_path = os.path.dirname(current_path)
            selected = 0

        elif key == ord("q"):
            break

        elif key == 10:
            selected_file = files[selected]

            full_path = os.path.join(current_path, selected_file)

            if os.path.isdir(full_path):
                current_path = os.path.abspath(full_path)
                selected = 0
            else:
                action = action_menu(stdscr, selected_file)

                try:
                    if action == "Öffnen":
                        subprocess.run(["xdg-open", full_path])

                    elif action == "Löschen":
                        os.remove(full_path)

                    elif action == "Verschieben":
                        ziel = input_box(stdscr, "Zielpfad:")
                        shutil.move(full_path, ziel)

                    elif action == "Kopieren":
                        ziel = input_box(stdscr, "Zielpfad:")
                        shutil.copy(full_path, ziel)

                    elif action == "Neuer Ordner":
                        name = input_box(stdscr, "Ordnername:")
                        os.mkdir(os.path.join(current_path, name))

                    elif action == "Neue Datei":
                        name = input_box(stdscr, "Dateiname:")
                        open(os.path.join(current_path, name), "w").close()

                    elif action == "Umbenennen":
                        neu = input_box(stdscr, "Neuer Name:")
                        os.rename(full_path, os.path.join(current_path, neu))

                    elif action == "Editor":
                        subprocess.run(["nano", full_path])

                    elif action == "Ausführen":
                        befehl = input_box(
                            stdscr,
                            "Befehl eingeben (z.B python3):"
                        )

                        cmd = befehl.split()
                        cmd.append(full_path)

                        curses.endwin()
                        subprocess.run(cmd)
                        input("ENTER drücken...")
                        stdscr.refresh()

                    elif action == "Auf USB kopieren":
                        usbs = find_usb()

                        if len(usbs) == 0:
                            input_box(stdscr, "Kein USB gefunden.")
                        else:
                            ziel = usbs[0]
                            shutil.copy(full_path, ziel)

                except Exception as e:
                    input_box(stdscr, f"Fehler: {e}")


if __name__ == "__main__":
    curses.wrapper(main)
