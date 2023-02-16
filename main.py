import os
import curses
import base64
import ctypes
from TermUI.ui import UI
from TermUI.text import Text
from TermUI.region import Region
from TermUI.button import Button
from TermUI.textbox import Textbox
from TermUI.position import Position
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def main(stdscr):
    os.system("title D-Word Password Manager")

    green = 42
    red = 204
    fernet = None

    def get_key(password):
        # FERNET KEY FROM STRING
        salt = os.urandom(0)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
        )
        return base64.urlsafe_b64encode(kdf.derive(bytes(password, encoding='utf-8')))

    def init_login_list():
        # CREATE THE LOGIN LIST ON THE RIGHT HALF OF THE MAIN SCREEN
        loginList.elements = []
        loginList.add_element(Text("Your saved logins:", Position(1, 0)))

        logins = {}

        for file in os.listdir("cache/services/"):
            try:
                service_name = fernet.decrypt(eval(file))
            except:
                continue
            with open(f"cache/services/{file}", "r") as f:
                lines = f.read().split("::")
                logins[service_name.decode("utf-8")] = {
                    "email": fernet.decrypt(eval(lines[0])),
                    "password": fernet.decrypt(eval(lines[1])),
                    "filename": file
                }

        for i, login in enumerate(logins):
            email = logins[login]['email']
            password = logins[login]['password']
            filename = logins[login]["filename"]
            text_element = Text(
                f"{login} > {email.decode('utf-8')}", Position(1, i+2))

            text_element.data = {
                "email": email.decode('utf-8'),
                "password": password.decode('utf-8'),
                "service": login,
                "filename": filename}

            if (i+1) % 2 == 0:
                text_element.color = 249
            text_element.callback = click_login

            edit_button = Text(
                "Edit", text_element.pack.get("right") + Position(1, 0))
            edit_button.color = 241
            edit_button.data["entry"] = text_element
            edit_button.callback = edit_entry
            edit_button.underlined = True

            delete_button = Text(
                "X", edit_button.pack.get("right") + Position(1, 0))
            delete_button.color = red
            delete_button.data["entry"] = text_element
            delete_button.callback = delete_entry
            delete_button.underlined = True

            loginList.add_element(delete_button)
            loginList.add_element(text_element)
            loginList.add_element(edit_button)

    def on_login(button):
        # WHEN THE LOGIN BUTTON IS PRESSED
        nonlocal fernet
        if not os.path.exists("cache/services"):
            os.makedirs("cache/services")
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(
                "cache", FILE_ATTRIBUTE_HIDDEN)

        if len(masterPassword.text) > 0:
            fernet = Fernet(get_key(masterPassword.text.strip()))
            init_login_list()
            loginViewer.elements = []

            clickLoginReminder = Text(
                "Click an email on the right to view the login.", Position(1, 0))
            clickLoginReminder.color = 13
            loginViewer.add_element(clickLoginReminder)
            mainScreen.draw()

            loginScreen.swap(mainScreen)

    def on_enter_masterPassword(textbox):
        # LOGIN WITH ENTER KEY ON LOGIN MENU
        on_login(textbox)

    def change_master_password(button):
        # CHANGE MASTER PASSWORD BUTTON
        masterPassword.reset()
        mainScreen.swap(loginScreen)

    def edit_entry(text):
        # EDIT ENTRY TEXT NEXT TO LOGIN LIST
        entry = text.data["entry"]

        # display and content are the same
        entryEditor.text = "Edit Entry"
        emailBox.text = emailBox.display = entry.data["email"]
        passwordBox.text = passwordBox.display = entry.data["password"]
        serviceBox.text = serviceBox.display = entry.data["service"]
        createNewEntry.set_text("Edit Entry")
        createNewEntry.data["old"] = entry.data

        createNewEntry.callback = edit_entry_button

        text.region.ui.draw()

    def delete_entry(text):
        # DELETE ENTRY BUTTON
        entry = text.data["entry"]
        os.remove(f"cache/services/{entry.data['filename']}")
        init_login_list()
        text.region.ui.draw()

    def create_new_entry(button):
        # CREATE ENTRY BUTTON
        with open(f"cache/services/{fernet.encrypt(bytes(serviceBox.text, encoding='utf-8'))}", "w+") as file:
            file.write(
                f"{fernet.encrypt(bytes(emailBox.text, encoding='utf-8'))}::{fernet.encrypt(bytes(passwordBox.text, encoding='utf-8'))}")
        emailBox.reset()
        passwordBox.reset()
        serviceBox.reset()

        init_login_list()

        button.region.ui.draw()

    def edit_entry_button(button):
        # ACTUALLY EDIT THE ENTRY
        os.remove(
            f"cache/services/{button.data['old']['filename']}")
        with open(f"cache/services/{fernet.encrypt(bytes(serviceBox.text, encoding='utf-8'))}", "w+") as file:
            file.write(
                f"{fernet.encrypt(bytes(emailBox.text, encoding='utf-8'))}::{fernet.encrypt(bytes(passwordBox.text, encoding='utf-8'))}")

        entryEditor.text = "Create new login"
        emailBox.reset()
        passwordBox.reset()
        serviceBox.reset()
        createNewEntry.set_text("Create New")
        createNewEntry.data = {}
        createNewEntry.callback = create_new_entry
        init_login_list()
        button.region.ui.draw()

    def spawn_aliens(_):
        # ALIEN EASTER EGG ON THE LOGIN MENU
        nonlocal aliens_spawned
        alien = "    .-\"\"\"\"-.\n   /        \\\n  /_        _\\\n // \      / \\\\\n \\\__\    /__//\n  \    ||    /\n   \        /\n    \  __  /\n     '.__.'\n      |  |\n      |  |"
        if aliens_spawned:
            return
        ALIEN_LINES = alien.split("\n")
        for i, line in enumerate(ALIEN_LINES):
            left_line = Text(line, Position(
                3, loginRegion.size.half().y-len(ALIEN_LINES)+i))
            left_line.color = 42
            right_line = Text(line, Position(
                95, loginRegion.size.half().y-len(ALIEN_LINES)+i))
            right_line.color = 42
            loginRegion.add_element(right_line)
            loginRegion.add_element(left_line)
        loginScreen.draw()
        aliens_spawned = True

    def toggle_loginViewer_data(button):
        # TOGGLE PASSWORD TEXT IN THE LOGIN VIEWER
        if not button.clicked:
            button.color = red
            loginViewer.elements[4].hidden = False

            loginViewer.elements[3].hidden = True
        else:
            button.color = green
            loginViewer.elements[4].hidden = True

            loginViewer.elements[3].hidden = False
        button.region.ui.draw()

    def obfuscate(text: str):
        # CREATE A HIDDEN STRING
        string = ""
        for _ in text:
            string += "*"
        return string

    def click_login(text):
        # WHEN YOU CLICK THE LOGIN IN THE LOGIN LIST
        loginViewer.elements = []
        loginViewer.text = text.data["service"]

        email = Text("Email: ", Position(1, 0))
        email.color = green
        loginViewer.add_element(email)

        email_data = Text(text.data["email"], Position(0, 0))
        email_data.start = email.pack.get("right")
        loginViewer.add_element(email_data)

        password = Text("Password: ", Position(1, 1))
        password.color = green
        loginViewer.add_element(password)

        password_data = Text(text.data["password"], Position(0, 0))
        password_data.start = password.pack.get("right")
        password_data.hidden = True
        loginViewer.add_element(password_data)

        scrambled = Text(obfuscate(text.data["password"]), Position(11, 0))
        scrambled.start = password.pack.get("right")
        scrambled.hidden = False
        loginViewer.add_element(scrambled)

        toggle = Button("∗", loginViewer.size -
                        Position(5, 3), toggle_loginViewer_data)
        toggle.color = red
        loginViewer.add_element(toggle)

        text.region.ui.draw()

    def show_password(button):
        # SHOW PASSWORD ON CREATE/EDIT LOGIN
        button.color = red
        button.data["element"].password = True
        if button.clicked:
            button.color = green
            button.data["element"].password = False
        button.region.ui.draw()

    aliens_spawned = False

    # LOGIN SCREEN
    title = " ______                   _______  _______  ______  \n(  __  \        |\     /|(  ___  )(  ____ )(  __  \ \n| (  \  )       | )   ( || (   ) || (    )|| (  \  )\n| |   ) | _____ | | _ | || |   | || (____)|| |   ) |\n| |   | |(_____)| |( )| || |   | ||     __)| |   | |\n| |   ) |       | || || || |   | || (\ (   | |   ) |\n| (__/  )       | () () || (___) || ) \ \__| (__/  )\n(______/        (_______)(_______)|_/  \___(_______/"
    loginScreen = UI(stdscr)
    loginRegion = Region("Login", Position(0, 0), Position(119, 29))
    loginRegion.framed = False

    # TITLE ASCII ART
    TITLE_LINES = title.split("\n")
    for i, line in enumerate(TITLE_LINES):
        position = Position(loginRegion.size.half().x-len(line)+23,
                            loginRegion.size.half().y-len(TITLE_LINES)+i)
        text_element = Text(line, position)
        text_element.callback = spawn_aliens
        loginRegion.add_element(text_element)

    # SUBTITLE
    subtitle_string = "The safety first offline password manager."
    subtitle = Text(subtitle_string, Position(
        loginRegion.size.half().x - len(subtitle_string) + 18,
        loginRegion.size.half().y))
    subtitle.color = 161
    loginRegion.add_element(subtitle)

    # MASTER PASSWORD
    masterPassword = Textbox(
        "",
        Position(loginRegion.size.half().x - 48 +
                 17, loginRegion.size.half().y+2),
        Position(48, 0))

    masterPassword.placeholder = f"Enter your master password. (<={masterPassword.maxchars} chars)"

    masterPassword.char_limit = masterPassword.maxchars

    masterPassword.password = True
    masterPassword.on_enter = on_enter_masterPassword
    loginRegion.add_element(masterPassword)

    # LOGIN BUTTON
    loginButton = Button("Login", masterPassword.pack.get(
        "right") + Position(1, 0), on_login)
    loginRegion.add_element(loginButton)

    # ADD REGION
    loginScreen.add_region(loginRegion)

    # MAIN HOME SCREEN AFTER LOGIN
    mainScreen = UI(stdscr)

    # MAIN REGION
    mainRegion = Region("", Position(0, 0), Position(119, 29))
    changeMasterPassword = Button(
        "Change Master Password", Position(1, 0), change_master_password)
    mainRegion.add_element(changeMasterPassword)

    # LOGIN LIST
    loginList = Region("Logins", Position(
        mainRegion.size.half().x+1, 0), Position(mainRegion.size.half().x, mainRegion.size.y+1))
    mainScreen.add_region(loginList)

    # LOGIN VIEWER
    loginViewer = Region("Create new login", changeMasterPassword.pack.get(
        "down") + Position(0, 2), Position(mainRegion.size.half().x, 4))

    # ENTRY EDITOR
    entryEditor = Region(
        "Create new login", loginViewer.pack.get("down") + Position(0, 9), Position(mainRegion.size.half().x, 10))

    # EMAIL
    emailBox = Textbox("Email", Position(1, 1), Position(35, 0))
    emailBox.char_limit = emailBox.maxchars
    emailBox.placeholder += f" (<={emailBox.maxchars})"
    entryEditor.add_element(emailBox)

    # PASSWORD
    passwordBox = Textbox(
        "Password", emailBox.pack.get("down"), Position(35, 0))
    passwordBox.char_limit = passwordBox.maxchars
    passwordBox.placeholder += f" (<={passwordBox.maxchars})"
    passwordBox.password = True
    entryEditor.add_element(passwordBox)

    # SERVICE NAME
    serviceBox = Textbox(
        "Service", emailBox.pack.get("right"), Position(20, 0))
    serviceBox.char_limit = 10
    serviceBox.placeholder += f" (<={serviceBox.char_limit})"
    entryEditor.add_element(serviceBox)

    # UNIQUE NAME WARNING
    uniqueWarning = Text("SERVICES MUST BE UNIQUE",
                         serviceBox.pack.get("up") - Position(2, 0))
    uniqueWarning.color = red
    uniqueWarning.underlined = True
    entryEditor.add_element(uniqueWarning)

    # CREATE/EDIT BUTTON
    createNewEntry = Button(
        "Create New", entryEditor.size - Position(16, 3), create_new_entry)
    createNewEntry.color = 42
    entryEditor.add_element(createNewEntry)

    # SHOW PASSWORD BUTTON
    showPassword = Button("∗", passwordBox.pack.get("right"), show_password)
    showPassword.data["element"] = passwordBox
    showPassword.color = red
    entryEditor.add_element(showPassword)

    # ADD REGIONS
    mainScreen.add_region(loginViewer)
    mainScreen.add_region(mainRegion)
    mainScreen.add_region(entryEditor)

    # ALWAYS ACTIVATE LAST
    loginScreen.activate()


if __name__ == "__main__":
    curses.wrapper(main)
