# Datei: pi_explorer_ultra.py
# Raspberry Pi Explorer ULTRA
# Voller Datei Explorer mit:
# - Blauem GUI
# - USB Support
# - Suche
# - ZIP/TAR Entpacken
# - Kopieren/Einfügen
# - Verschieben
# - Löschen
# - Umbenennen
# - Neue Dateien/Ordner
# - Datei Ausführen
# - Nano Editor

import curses
import os
import shutil
import subprocess
import zipfile
import tarfile

current_path = os.path.expanduser("~")

selected = 0
scroll_offset = 0

clipboard = None
clipboard_mode = None

search_text = ""


# =========================
# DATEIEN LADEN
# =========================

def get_files(path):

    try:

        files = os.listdir(path)

        files.sort()

        if search_text:

            files = [
                f for f in files
                if search_text.lower() in f.lower()
            ]

        return [".."] + files

    except:

        return [".."]


# =========================
# USB FINDEN
# =========================

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


# =========================
# EINGABE
# =========================

def input_box(stdscr, text):

    curses.echo()

    stdscr.clear()

    stdscr.addstr(0, 0, text)

    stdscr.refresh()

    value = stdscr.getstr(2, 0).decode("utf-8")

    curses.noecho()

    return value


# =========================
# NACHRICHT
# =========================

def message(stdscr, text):

    stdscr.clear()

    stdscr.addstr(0, 0, text)

    stdscr.addstr(2, 0, "ENTER drücken")

    stdscr.refresh()

    stdscr.getch()


# =========================
# MENÜ
# =========================

def menu(stdscr, title, options):

    choice = 0

    while True:

        stdscr.clear()

        stdscr.addstr(0, 0, title)

        for i, option in enumerate(options):

            if i == choice:

                stdscr.attron(curses.A_REVERSE)

                stdscr.addstr(i + 2, 0, option)

                stdscr.attroff(curses.A_REVERSE)

            else:

                stdscr.addstr(i + 2, 0, option)

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP:

            choice = (choice - 1) % len(options)

        elif key == curses.KEY_DOWN:

            choice = (choice + 1) % len(options)

        elif key == 10:

            return options[choice]


# =========================
# USB AUSWAHL
# =========================

def choose_usb(stdscr):

    usbs = find_usb()

    if not usbs:

        message(stdscr, "Kein USB Stick gefunden")

        return None

    return menu(stdscr, "USB auswählen", usbs)


# =========================
# DATEI EINFÜGEN
# =========================

def paste():

    global clipboard
    global clipboard_mode
    global current_path

    if not clipboard:

        return

    name = os.path.basename(clipboard)

    target = os.path.join(current_path, name)

    if clipboard_mode == "copy":

        if os.path.isdir(clipboard):

            shutil.copytree(clipboard, target)

        else:

            shutil.copy2(clipboard, target)

    elif clipboard_mode == "move":

        shutil.move(clipboard, target)

        clipboard = None
        clipboard_mode = None


# =========================
# GUI ZEICHNEN
# =========================

def draw(stdscr, files):

    global selected
    global scroll_offset

    stdscr.clear()

    h, w = stdscr.getmaxyx()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

    stdscr.bkgd(" ", curses.color_pair(1))

    top = f" Raspberry Pi Explorer ULTRA | {current_path}"

    stdscr.addstr(
        0,
        0,
        top[:w - 1],
        curses.color_pair(2)
    )

    stdscr.addstr(
        1,
        0,
        f"Suche: {search_text}"[:w - 1]
    )

    if clipboard:

        clip = f"Zwischenablage: {os.path.basename(clipboard)} ({clipboard_mode})"

        stdscr.addstr(2, 0, clip[:w - 1])

    help_lines = [
        "HOCH/RUNTER = Scrollen",
        "ENTER = Menü",
        "BACKSPACE = Zurück",
        "S = Suche",
        "U = USB",
        "P = Einfügen",
        "Q = Ende"
    ]

    for i, line in enumerate(help_lines):

        stdscr.addstr(
            h - len(help_lines) + i - 1,
            0,
            line[:w - 1],
            curses.color_pair(2)
        )

    visible = h - 12

    if selected < scroll_offset:

        scroll_offset = selected

    if selected >= scroll_offset + visible:

        scroll_offset = selected - visible + 1

    for idx in range(
        scroll_offset,
        min(len(files), scroll_offset + visible)
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


# =========================
# DATEI STARTEN
# =========================

def run_file(stdscr, path):

    options = [
        "python3",
        "bash",
        "sh",
        "xdg-open",
        "./datei",
        "Eigener Befehl"
    ]

    action = menu(stdscr, "Datei starten mit", options)

    curses.endwin()

    try:

        if action == "python3":

            subprocess.run(["python3", path])

        elif action == "bash":

            subprocess.run(["bash", path])

        elif action == "sh":

            subprocess.run(["sh", path])

        elif action == "xdg-open":

            subprocess.run(["xdg-open", path])

        elif action == "./datei":

            subprocess.run(["chmod", "+x", path])

            subprocess.run([path])

        elif action == "Eigener Befehl":

            cmd = input("Befehl: ")

            subprocess.run(cmd.split() + [path])

    except Exception as e:

        print("Fehler:", e)

    input("ENTER drücken...")


# =========================
# EXTRAHIEREN
# =========================

def extract_archive(stdscr, full):

    extract_folder = os.path.join(
        current_path,
        "extrahiert"
    )

    os.makedirs(
        extract_folder,
        exist_ok=True
    )

    try:

        if full.endswith(".zip"):

            with zipfile.ZipFile(full, "r") as zip_ref:

                zip_ref.extractall(extract_folder)

            message(stdscr, "ZIP entpackt!")

        elif (
            full.endswith(".tar")
            or full.endswith(".tar.gz")
            or full.endswith(".tgz")
        ):

            with tarfile.open(full) as tar_ref:

                tar_ref.extractall(extract_folder)

            message(stdscr, "Archiv entpackt!")

        else:

            message(
                stdscr,
                "Format nicht unterstützt"
            )

    except Exception as e:

        message(stdscr, f"Fehler: {e}")


# =========================
# HAUPTPROGRAMM
# =========================

def main(stdscr):

    global current_path
    global selected
    global clipboard
    global clipboard_mode
    global search_text

    curses.curs_set(0)

    stdscr.keypad(True)

    while True:

        files = get_files(current_path)

        if selected >= len(files):

            selected = len(files) - 1

        draw(stdscr, files)

        key = stdscr.getch()

        # RUNTER
        if key == curses.KEY_DOWN:

            selected = min(
                len(files) - 1,
                selected + 1
            )

        # HOCH
        elif key == curses.KEY_UP:

            selected = max(
                0,
                selected - 1
            )

        # SUCHE
        elif key == ord("s"):

            search_text = input_box(
                stdscr,
                "Suche eingeben:"
            )

            selected = 0

        # USB
        elif key == ord("u"):

            usb = choose_usb(stdscr)

            if usb:

                current_path = usb

                selected = 0

        # EINFÜGEN
        elif key == ord("p"):

            try:

                paste()

            except Exception as e:

                message(
                    stdscr,
                    f"Fehler: {e}"
                )

        # ZURÜCK
        elif key == curses.KEY_BACKSPACE or key == 127:

            current_path = os.path.dirname(current_path)

            selected = 0

        # ENDE
        elif key == ord("q"):

            break

        # ENTER
        elif key == 10:

            file = files[selected]

            full = os.path.join(
                current_path,
                file
            )

            is_folder = os.path.isdir(full)

            if is_folder:

                options = [
                    "Öffnen",
                    "Kopieren",
                    "Verschieben",
                    "Umbenennen",
                    "Löschen",
                    "Neue Datei",
                    "Neuer Ordner",
                    "Zurück"
                ]

            else:

                options = [
                    "Ausführen",
                    "Editor",
                    "Extrahieren",
                    "Kopieren",
                    "Verschieben",
                    "Umbenennen",
                    "Löschen",
                    "Zurück"
                ]

            action = menu(
                stdscr,
                file,
                options
            )

            try:

                # ÖFFNEN
                if action == "Öffnen":

                    current_path = full

                    selected = 0

                # AUSFÜHREN
                elif action == "Ausführen":

                    run_file(
                        stdscr,
                        full
                    )

                # EDITOR
                elif action == "Editor":

                    curses.endwin()

                    subprocess.run(
                        ["nano", full]
                    )

                # EXTRAHIEREN
                elif action == "Extrahieren":

                    extract_archive(
                        stdscr,
                        full
                    )

                # KOPIEREN
                elif action == "Kopieren":

                    clipboard = full
                    clipboard_mode = "copy"

                # VERSCHIEBEN
                elif action == "Verschieben":

                    clipboard = full
                    clipboard_mode = "move"

                # UMBENENNEN
                elif action == "Umbenennen":

                    new_name = input_box(
                        stdscr,
                        "Neuer Name:"
                    )

                    os.rename(
                        full,
                        os.path.join(
                            current_path,
                            new_name
                        )
                    )

                # LÖSCHEN
                elif action == "Löschen":

                    if os.path.isdir(full):

                        shutil.rmtree(full)

                    else:

                        os.remove(full)

                # NEUE DATEI
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

                # NEUER ORDNER
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

                message(
                    stdscr,
                    f"Fehler: {e}"
                )

    curses.endwin()


# =========================
# START
# =========================

if __name__ == "__main__":

    curses.wrapper(main)
