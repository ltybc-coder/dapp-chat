from config import *
import datetime
import logging

from server import Server


def server_start():
    serv = Server(HOST, PORT)
    logging.info(f'Server started and working')
    serv.start()
