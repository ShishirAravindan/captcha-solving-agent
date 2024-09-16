#!python3 

import utils, agent
import logging, logging.config
import sys
import json
import state
from selenium.common.exceptions import ElementClickInterceptedException
import time
import more_itertools
from multiprocessing import Process

STATE_FILE_PATH = '../data/2_salariesUoIstate_2023.json'

def manual_process(URL, chunk):
    driver = utils.make_connection(URL, None)
    logging.info("PAGE LOADING")
    

    for name, _ in chunk.items():
        
        try:
            logging.info(f"---------GETTING FACULTY INFORMATION FOR {name}---------")
            time.sleep(20)
            # driver = utils.fill_form(driver, name)
            driver, chunk[name] = utils.get_faculty_department(driver, name)
            time.sleep(40)
            
            logging.info(f'FACULTY DEPT for {name}: {chunk[name]}')
            logging.info(f"---------WRITING RESULTS TO STATE FILE---------")
            state.update_state_file(STATE_FILE_PATH, chunk)
        except Exception as e:
            logging.error(f'Exception when filling form: {e}')

def process(URL, chunk):
    driver = utils.make_connection(URL, None)
    logging.info("PAGE LOADING")
    

    for name, _ in chunk.items():
        logging.info(f"---------GETTING FACULTY INFORMATION FOR {name}---------")
        driver = utils.fill_form(driver, name)
        try:
            chunk[name] = utils.get_faculty_department(driver, name)
            logging.info(f'FACULTY DEPT for {name}: {chunk[name]}')
            logging.info(f"---------WRITING RESULTS TO STATE FILE---------")
            state.update_state_file(STATE_FILE_PATH, chunk)
        except ElementClickInterceptedException as e:
            driver = agent.captcha_workflow(driver)
            logging.info("CAPTCHA COMPLETED")
            chunk[name] = utils.get_faculty_department(driver, name)
            logging.info(f'FACULTY DEPT for {name}: {chunk[name]}')
            logging.info(f"---------WRITING RESULTS TO STATE FILE---------")
            state.update_state_file(STATE_FILE_PATH, chunk)

    

def single_process(config_file, chunk):
    logging.config.fileConfig("test_log.ini")
    with open(config_file, 'r') as file:
        config = json.load(file)
    # process(config["URL"], chunk)
    manual_process(config["URL"], chunk)

def get_chunk_slices(chunks, n):
    return more_itertools.divide(n, chunks.items())


def main():
    if len(sys.argv) != 2:
        print("Usage: ./main.py <config_file>")
        sys.exit(1)
    config_file = sys.argv[1:][0]
    processes = []
    NUM_PROCESSES = 2
    chunks = state.get_fresh_chunk(STATE_FILE_PATH, 5*NUM_PROCESSES)
    chunks = get_chunk_slices(chunks, 5)
    # print(f"{chunks}, {type(chunks)}")
    for i in range(NUM_PROCESSES):
        p = Process(target=single_process, args=(config_file, dict(chunks[i]), ))
        p.start()
        processes.append(p)
    for p in processes:
        p.join()


if __name__ == "__main__":
    main()