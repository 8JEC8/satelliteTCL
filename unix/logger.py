import time


class Logger:
    Printer = print
    def __init__(self, name, filedir):
        #self.file = open(filedir, "w")
        self.name = name

    def __print(self, message, level_prefix, override=False):
        t = time.gmtime()
        # [DD/MM/YY][HH:MM:SS][Name/INFO]: MSG
        msg = f'[{t[3]:02}:{t[4]:02}:{t[5]:02}][{self.name}/{level_prefix}]: {message}\n'
        if override:
            print(msg)
        else:
            self.Printer(msg)

    def info(self, message):
        self.__print(message, 'INFO')

    def warn(self, message):
        self.__print(message, 'WARN')

    def debug(self, message):  # Keep spam on separate terminal
        self.__print(message, 'DEBUG', override=True)

    def error(self, message):
        self.__print(message, 'ERROR')
