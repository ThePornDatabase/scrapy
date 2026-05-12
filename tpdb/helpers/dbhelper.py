from configparser import ConfigParser
import psycopg2


def db_config(filename='database_tpdb.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


def db_conn():
    db = db_config()
    conn = psycopg2.connect(**db)
    conn.autocommit = True
    cursor = conn.cursor()
    return conn, cursor
