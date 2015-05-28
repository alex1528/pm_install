# -*- coding: utf-8 -*-


def authenticate_decorator(func):
    def __authenticate_decorator(*args, **kwargs):
        self = args[0]
        user_email = self.get_secure_cookie("nosa_user")
        if user_email:
            fs = user_email.split("@")
            if fs[1] != "nosa.me":
                self.clear_cookie("nosa_user")
                self.write(
                    "You have to login with your nosa.me account...")
                return
            else:
                apply(func, args, kwargs)
        else:
            self.redirect("/login")

    return __authenticate_decorator
