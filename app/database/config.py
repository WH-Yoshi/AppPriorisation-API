from configparser import ConfigParser
import os
from dotenv import load_dotenv

load_dotenv()

filename = os.getenv('CONFIG_FILE') or './app/database/database.ini'

def load_config(section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
        return config
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
