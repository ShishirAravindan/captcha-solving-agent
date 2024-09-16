#!python3

import utils
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import logging.config
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from decaptcha import decaptcha
import time

config = {
    "iframe": "/html/body/div/div[2]/iframe",
    "captcha_instructions": "strong:nth-child(1)",
    "captcha_image_src": "img.rc-image-tile",
    "image_grid": "div.rc-image-tile-wrapper",
    "verify_button": "#recaptcha-verify-button" 
}

def captcha_workflow(driver: WebDriver):
    grid_size, payload, driver = _identify_and_extract_captcha_form(driver)
    if payload:
        target_class, images = payload[0], payload[1]
        img_path = utils._download_image_locally(images)
        _solve_captcha(driver, target_class, img_path, grid_size)
    return driver


def _solve_captcha(driver: WebDriver, target_class: str, img_path: str, grid_size: int):
    captcha_predictions = decaptcha(target_class, img_path, grid_size)
    _click_images(driver, captcha_predictions)
    _complete_form(driver)
    driver.switch_to.default_content()

def _identify_and_extract_captcha_form(driver: WebDriver):
    try:
        captcha_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, config["iframe"]))
        )
        grid_size, payload, driver = _extract_captcha_details(driver, captcha_iframe)
        return grid_size, payload, driver
    except NoSuchElementException as e:
        logging.error(f"solve_captcha exception: {e.msg}")
    except TimeoutException as e:
        logging.info(f"No CAPTCHA found on page {e.msg}")
    return None, None, driver

def _extract_captcha_details(driver: WebDriver, captcha_iframe: WebElement):
    try:
        driver.switch_to.frame(captcha_iframe)
        target_class, driver = _get_target_class(driver)
        grid_size, images_src, driver = _get_images(driver)
        return grid_size, [target_class, images_src], driver
    except Exception as e:
        logging.error(f"solve_captcha exception: {e}")
        driver.switch_to.default_content()
    return None, driver

def _get_target_class(driver):
    try:
        instruction_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config["captcha_instructions"]))
        )
        logging.info(f"CAPTCHA iFrame identified. Extracting info ...")
        logging.info(f"CAPTCHA target: {instruction_element.text}")
        return instruction_element.text, driver
    except Exception as e:
        logging.error(f"Error Processing CAPTCHA form's instructions: {e}")
    return None, driver

def _get_images(driver):
    try:
        images_table_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 
                                            f'{config["captcha_image_src"]}-33'))
        )
        images_src = images_table_element.get_attribute("src")
        logging.info(f"3x3 CAPTCHA image grid identified")
        return 3, images_src, driver
    except NoSuchElementException as e:
        logging.error(f"[NoSuchElementException] Error Processing CAPTCHA form's images: {e}")
        logging.info(f"4x4 CAPTCHA image grid identified. [Need to process]")
    except TimeoutException as e:
        logging.debug(f"No 3x3 CAPTCHA image grid identified.")
        try:
            images_table_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                                                f'{config["captcha_image_src"]}-44'))
            )
            images_src = images_table_element.get_attribute("src")
            logging.info(f"4x4 CAPTCHA image grid identified")
            return 4, images_src, driver
        except NoSuchElementException as e:
            logging.error(f"[NoSuchElementException] Error Processing CAPTCHA form's images: {e}")
        except TimeoutException as e:
            logging.debug(f"No 4x4 CAPTCHA image grid identified. {e}")
    return None, '', driver

def _click_images(driver: WebDriver, preds: list[int]) -> WebDriver:
    """Given the driver and the results (i.e. predictions from the vLLM) click
    the corresponding tiles in the captcha form.

    For easier testing just use a dummy list for results
    eg: r = [0, 0, 0, 0, 1, 1, 1, 0, 1]
    should click the middle, middle-right, bottom-left and bottom-right
    then should hit the verify button
    """
    try:
        image_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, config["image_grid"]))
        )
        for i, pred in enumerate(preds):
            if pred == True: image_elements[i].click()
    except NoSuchElementException as e:
        logging.error(f"Error: Could not find image elements with selector '{config['image_grid']}'. {e}")
    except Exception as e:
        logging.error(f"Error: Could not click the image elements. {e}")
    return driver

def _complete_form(driver: WebDriver) -> WebDriver:
    try:
        verify_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, config["verify_button"]))
        )
        verify_button.click()
    except NoSuchElementException as e:
        print(f"Error: Could not find the verify button with selector '{config['verify_button']}'. {e}")
    except Exception as e:
        print(f"Error: Could not click the verify button. {e}")
    return driver

#--------------------------------------------------------------------------------
# Test code
def test_main():
    logging.config.fileConfig("test_log.ini")
    URL = "https://iam.uiowa.edu/whitepages/search"
    name = "THOMAS S GRUCA"
    logging.info("PAGE LOADING")
    driver = utils.make_connection(URL, None)
    driver = utils.fill_form(driver, name)
    logging.info("FORM FILLED")
    captcha_workflow(driver)
    logging.info("CAPTCHA reached")

    # TODO: All other test case
        
    
if __name__ == "__main__":
    test_main()