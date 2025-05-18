import time

class Logger:
    def __init__(self, name, filedir):
        self.file = open(filedir, "w")
        self.name = name

    def __print(self, message, level_prefix):
        t = time.gmtime()
        # [DD/MM/YY][HH:MM:SS][Name/INFO]: MSG
        print(f'[{t[2]:02}/{t[1]:02}/{t[0]}][{t[3]:02}:{t[4]:02}:{t[5]:02}][{self.name}/{level_prefix}]: {message}')
        # not writing yet to not waste space

    def info(self, message):
        self.__print(message, 'INFO')

    def warn(self, message):
        self.__print(message, 'WARN')

    def debug(self, message):
        if True:
            self.__print(message, 'DEBUG')

    def error(self, message):
        self.__print(message, 'ERROR')
