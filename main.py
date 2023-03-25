import json
from hashlib import sha256
from datetime import datetime
from typing import Union
import sys
import subprocess


"""
    PyCharm users will need to enable “emulate terminal” in output console option in
    run/debug configuration to see styled output.
    
    Run > Edit Configurations > Check the option: Emulate terminal in output console
"""


"""
Controls (required login)
    for normal user:
        - profile
            check current account's informations
        
        - edit profile
            edit current account's informations
        
        - logout
            logout the current account
            
        - exit
            exit the program
    
    for admin:
        - list
            list all the users
            
        - delete <account index>
            delete a specific user with the index according to the "list" command's table
"""


try:
    import rich
    from rich.table import Table
    from rich.prompt import Confirm
    from rich.prompt import Prompt

except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'rich'])

finally:
    import rich
    from rich.table import Table
    from rich.prompt import Confirm
    from rich.prompt import Prompt


class Encrypt:
    def __init__(self, information, validate, error_message):
        self.error_message = error_message
        self.encrypt = information
        self.validate = validate

    @property
    def encrypt(self):
        return self._information

    @encrypt.setter
    def encrypt(self, value):
        if self.validate(value):
            self._information = sha256(bytes(value, "ascii")).hexdigest()
        else:
            self._information = False


class Password(Encrypt):
    def __init__(self, password):
        super().__init__(
            password,
            self.validate,
            "Password must include numbers, upper and lower case characters",
        )

    @staticmethod
    def validate(password):
        conditions = [
            lambda pw: any(char.isupper() for char in pw),
            lambda pw: any(char.islower() for char in pw),
            lambda pw: any(char.isdigit() for char in pw)
        ]

        return all(condition(password) for condition in conditions)


class Email(Encrypt):
    def __init__(self, email):
        self.admin_encryt = email
        super().__init__(
            email,
            self.validate,
            "Invalid email format."
        )

    @property
    def admin_encryt(self):
        return self._admin_use_email

    @admin_encryt.setter
    def admin_encryt(self, email):
        if self.validate(email):
            self._admin_use_email = email.replace( email[ 2: (i := email.index("@")) ], "*"*(i-2) )
        else:
            self._admin_use_email = "Invalid email format."

    @staticmethod
    def validate(email):
        if ("@" in email) and email.endswith(".com"):
            return email


class User_Information:
    def __init__(self, username, email, password):
        self.email = email
        self.user_info = {
            "username": username,
            "email": {
                "user": Email(self.email).encrypt,
                "admin": Email(self.email).admin_encryt
            },
            "password": Password(password).encrypt,
            "date": str(datetime.now())
        }

    def save(self):
        try:
            with open("data.json", "r+") as file:
                data = json.load(file)
                data.append(self.user_info)
                file.seek(0)
                json.dump(data, file, indent=4)

            return self.user_info

        except FileNotFoundError:
            json.dump([self.user_info], open("data.json","w"), indent=4)
            return self.user_info

    @staticmethod
    def check_if_exist(email):
        email = Email(email)

        if not email.encrypt:
            return email.error_message

        try:
            with open("data.json", "r") as file:
                for user in json.load(file):
                    if user["email"]["user"] == email.encrypt:
                        return user

        except FileNotFoundError:
            return

class Admin_menu:
    @staticmethod
    def list_user():
        table = Table(
            "No",
            "Username",
            "Email",
            "Register Date",
            title="User List",
            header_style="bold blue"
        )

        with open("data.json", "r") as file:
            user_count = 0

            for user in json.load(file):
                user_count += 1

                table.add_row(
                    f"{user_count}",
                    user["username"],
                    user["email"]["admin"],
                    user["date"]
                )

        rich.console.Console().print(table)

    @staticmethod
    def delete_user(admin, index):
        with open("data.json", "r") as file:
            data = json.load(file)

            if len(data) < index:
                return "Index out of the range."

        with open("data.json", "w") as file:
            user = data.pop(index-1)

            if len(data) == 0:
                json.dump([], file, indent=4)
                Main.status = False

            file.seek(0)
            json.dump(data, file, indent=4)

            if admin == user["email"]["user"]:
                main.login_status = False
                main.user = None

            return f"{user['username']} has been removed"


class User_menu:
    def __init__(self, user):
        self.user = user

    def user_profile(self):
        return(
            "\n"
            "User Profile:\n"
            f"\tUsername: {self.user['username']}\n" 
            f"\tEmail: {self.user['email']['admin']}\n" 
            f"\tRegister Date: {self.user['date']}\n"
        )


    def validate(self, _email, password):
        password = Password(password)
        email = Email(_email)

        if not password.encrypt:
            return password.error_message

        elif not email.encrypt:
            return email.error_message

        elif User_Information.check_if_exist(_email) \
                and self.user["email"]["user"] != email.encrypt:
            return "Email has already taken."

        else:
            return email.encrypt, password.encrypt


    def get_data_index(self, data: list):
        for item in data:
            if item["email"]["user"] == self.user["email"]["user"]:
                return data.index(item)


    def edit_profile(self, username, email, password):
        if not any([username, email, password]):
            return "", None

        if type(message := self.validate(email, password)) != tuple:
            return message, None

        else:
            _email, password = message

        new_profile = {
            "username": self.user["username"] if not username else username,
            "email": {
                "user":
                    self.user["email"]["user"] if not email else _email,
                "admin":
                    self.user["email"]["admin"] if not email else Email(email).admin_encryt
            },
            "password": self.user["password"] if not password else password,
            "date": self.user["date"],
        }

        with open("data.json", "r+") as file:
            data = json.load(file)
            data[self.get_data_index(data)] = new_profile
            file.seek(0)
            json.dump(data, file, indent=4)

        return (
                "\n"
                "Updated:\n"
                f"\tUsername: {new_profile['username']}\n"
                f"\tEmail: {new_profile['email']['admin']}\n"
            ), new_profile


def register(username, email, password):
    registeration = User_Information(username, email, password)

    if message := registeration.check_if_exist(email):
        if type(message) == dict:
            yield "Email has already taken."
            return

        else:
            yield message
            return

    else:
        yield "Congratulation, your account has been successfully created."
        yield registeration.save()


def login(email, _password):
    password = Password(_password)
    user: Union[dict, str] = User_Information.check_if_exist(email)

    if not password.encrypt:
        yield password.error_message
        return

    if not Email.validate(email):
        yield user
        return

    if not user or (user["password"] != password.encrypt):
        yield "Invalid email or password. \n\nDon't have an account? Register Now!"
        return

    else:
        yield f"Welcome back, {user['username']}."
        yield user


class Main:
    status = True
    login_status = False
    user = None

    @staticmethod
    def pprint(value):
        rich.console.Console().print(
            value,
            style="bold blue"
        )

    def login_account(self):
        print("Login Page")
        email = Prompt.ask(prompt="Email")
        password = Prompt.ask(prompt="Password")
        user = login(email, password)

        self.pprint(_user := next(user))

        if "Welcome back" in _user:
            self.user = next(user)
            self.login_status = True

    def signup_account(self):
        print("Sign Up Page")
        username = Prompt.ask(prompt="Username")
        email = Prompt.ask(prompt="Email")
        password = Prompt.ask(prompt="Password")
        user = register(username, email, password)

        self.pprint(_user := next(user))

        if "Congratulation" in _user:
            self.user = next(user)
            self.login_status = True

    def mainloop(self):
        while self.status:
            while not self.login_status:
                if Confirm.ask("Do you have an account?"):
                    self.login_account()
                else:
                    self.signup_account()

            if message := self.command(self.user):
                self.pprint(message)


    def command(self, user):
        user_input = input(f"{user['username']}>").lower().strip()

        if user_input == "profile":
            return User_menu(user).user_profile()

        elif user_input == "edit profile":
            print(
                "Enter your new info, "
                "leave it blank if you do not want to change\n"
            )

            return_message, new_profile = User_menu(user).edit_profile(
                username=input("New username: "),
                email=input("New email: "),
                password=input("New password: ")
            )

            self.user = user if not new_profile else new_profile
            return return_message

        elif user_input == "":
            return

        elif user_input == "exit":
            self.status = False

        elif user_input == "logout":
            self.login_status = False
            self.user = None

        elif (admin_input := user_input.split())[0] == "admin":
            try:
                if admin_input[1] == "list":
                    Admin_menu.list_user()

                elif admin_input[1] == "delete" and admin_input[2].isdigit():
                    return Admin_menu.delete_user(self.user["email"]["user"], int(admin_input[2]))

            except IndexError:
                return (
                    "\n"
                    "- list\n"
                    "- delete <account index>\n"
                )

        else:
            return (
                "\n"
                "- profile\n"
                "- edit profile\n"
                "- logout\n"
                "- exit\n"
            )


if __name__ == "__main__":
    main = Main()
    main.mainloop()