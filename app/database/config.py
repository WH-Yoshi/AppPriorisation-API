from configparser import ConfigParser
import os
from dotenv import load_dotenv

load_dotenv()

filename = os.getenv('CONFIG_FILE')

import os
from configparser import ConfigParser # Assuming you are using configparser for .ini files

def load_config(section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        for item, value in parser.items(section):
            db[item] = value
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    # --- IMPORTANT CHANGE HERE ---
    # Try to get the password from an environment variable
    # If not found in environment, you might consider a fallback or raise an error
    db_password = os.getenv('POSTGRES_PASSWORD')
    if db_password:
        db['password'] = db_password
    else:
        # This is crucial: if DB_PASSWORD is not set, your app needs to know.
        # You could raise an error, or if you had a default, use it (not recommended for prod passwords).
        raise Exception("DB_PASSWORD environment variable not set!")

    return db
