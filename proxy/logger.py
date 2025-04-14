import time

class Logger:
    def __init__(self, name, filedir):
        self.file = open(filedir, "w")
        self.name = name

    def info(self, message):
        # [DD/MM/YY][HH:MM:SS][Name/INFO]: MSG
        t = time.gmtime()
        print(f'[{t[2]:02}/{t[1]:02}/{t[0]}][{t[3]:02}:{t[4]:02}:{t[5]:02}][{self.name}/INFO]: {message}'))
        # not writing yet to not waste space
