from multiprocessing import Process
import time
import logging
import client
import server_starter

if __name__ == '__main__':
    try:
        logging.basicConfig(filename='../chat.log', encoding='utf-8', level=logging.DEBUG)
    except ValueError:
        logging.basicConfig(filename='../chat.log', level=logging.DEBUG)
    proc = Process(target=server_starter.server_start)
    proc.start()

    time.sleep(0.2)
    client.client_start()
