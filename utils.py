#!python3

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import random
import json
import time
import requests
from PIL import Image
from io import BytesIO
import logging
import uuid
from typing import Tuple

def assert_equal(tc_name: str, arr1: list[bool], arr2: list[bool]):
    if _is_equal(arr1, arr2): return
    print (f"assert_equal failed: {tc_name}, {arr1}, {arr2}")

def _is_equal(arr1: list[bool], arr2: list[bool]) -> bool:
    if len(arr1) != len(arr2): return False
    for i in range(len(arr1)):
        if arr2[i] is not None and arr1[i] != arr2[i]: return False
    return True

def _download_image_locally(url) -> str:
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        fileName = f"temp/captcha_{uuid.uuid4().hex}.jpg"
        image.save(fileName)
    return fileName

def _generate_random(x, y):
    return random.uniform(x, y)

def _setup_driver(isHeadless: False):
    firefox_options = Options()
    firefox_options.set_preference("dom.popup_maximum", 0)
    firefox_options.set_preference("privacy.popups.disable_from_plugins", 3)
    if isHeadless: firefox_options.add_argument("--headless")  # Uncomment this line if you need to run the script in headless mode
    return webdriver.Firefox(options=firefox_options)

def _wait_for_elements(driver, path_name, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, path_name))
    )

def make_connection(URL, elementName, isHeadless=False):
    driver = _setup_driver(isHeadless)
    driver.get(URL)
    if elementName:
        _wait_for_elements(driver, elementName)
    return driver

def fill_form(driver: WebDriver, name: str):
    try:
        time.sleep(_generate_random(0.5, 3.5))
        name_field = driver.find_element(By.NAME, 'SearchEntry')
        name_field.clear()
        name_field.send_keys(name)
        time.sleep(_generate_random(0.5, 1.8))
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        logging.info(f"\nFORM FILLED with {name}")
    except TimeoutException as e:
        print("TimeoutException", e)
    except NoSuchElementException as e:
        print("NoSuchElementException", e)
    return driver 

def get_faculty_department(driver: WebDriver, name: str) -> Tuple[WebDriver, str]:
    last_name, first_middle = name.split(',')

    # Split the first and middle names
    first_middle_split = first_middle.split()

    # Check if there is a middle name
    if len(first_middle_split) == 2:
        first_name, middle_name = first_middle_split
        shortened_name = f"{last_name},{first_name} {middle_name[0]}."
    else:
        first_name = first_middle_split[0]
        shortened_name = f"{last_name},{first_name}"
    logging.info(f"The name being sent is {shortened_name}")
    name_field = driver.find_element(By.NAME, 'SearchEntry')
    name_field.clear()
    name_field.send_keys(shortened_name)
    time.sleep(_generate_random(0.5, 1.8))  # Adding a pause to simulate human interaction
    submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_button.click()
    time.sleep(_generate_random(0.5, 1.8))
    try:
        table = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.table'))
        )
        tr_tags = table.find_elements(By.TAG_NAME, 'tr')
        for tr in tr_tags:
            if tr.text.startswith('Campus Mail Address'):
                dept = tr.text.strip('\n').split('\n')[1].strip()
                logging.info(dept)
                return driver, dept
        else:
            logging.error(f"Not enough rows in the table.")
            return driver, "special condition"
    except Exception as e:
        logging.error(f"Table not Found or other error: {e}")
        return driver, "No department found"
