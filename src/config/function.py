
from configparser import ConfigParser

import os

import personaai_default as pdl

log = pdl.get_logger()

def mkdir(path):
    try:
        abspath = os.path.abspath(path)
        if not os.path.exists(f'{abspath}'):
            os.makedirs(f'{abspath}')

        log.info(f'"{abspath}" directory is created')
    except Exception as e:
        log.error(f'{e.__class__.__name__}: {e}')

class Config():
    global python_file_path

    def __init__(self, filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')):
        self.config = ConfigParser()
        self.config.read(filename)

        if not self.config:
            print('설정 파일이 존재하지 않습니다.')

    def get_target(self, target):
        return self.config[target]

    def get_property(self, target, property):
        return self.config[target][property]