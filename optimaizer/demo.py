# To download chromedriver, get the version of your chrome browser chrome://settings/help
# and download the corresponding chromedriver from https://googlechromelabs.github.io/chrome-for-testing/


import textwrap
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
import time
import random


def type_like_human(
    element: WebElement, text: str, min_delay: float = 0.05, max_delay: float = 0.10
) -> None:
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))  # Random delay for realism


def press_enter(element: WebElement) -> None:
    time.sleep(0.5)
    element.send_keys(Keys.SHIFT, Keys.RETURN)


def get_chatbot_messages(driver: webdriver.Chrome) -> list[str]:
    chatbot_messages = driver.find_elements(By.CLASS_NAME, "bot-message")
    return [message.text for message in chatbot_messages]


def wait_for_chatbot_answer(
    driver: webdriver.Chrome, count_chat_bot_messages: int
) -> None:
    while True:
        chatbot_messages = get_chatbot_messages(driver)
        time.sleep(0.5)
        if len(chatbot_messages) > count_chat_bot_messages:
            time.sleep(
                10
            )  # Wait for the chatbot to finish typing (which can be fairly long)
            count_chat_bot_messages = len(chatbot_messages)
            break


def main() -> None:
    # Get size of the screen: ``` system_profiler SPDisplaysDataType | grep Resolution ```
    WINDOW_WIDTH = 3456 // 4
    WINDOW_HEIGHT = 2234

    USER_MESSAGES = [
        """
        Optimize pricing for the following products: product-A, product-B, product-C

        Inventory levels are:
        - product-A: 90
        - product-B: 55
        - product-C: use default value
        """,
        # -------------------------------
        """
        Do the same for product-A and product-B only. Keep the same inventory level, but change the market size for product-A to 1000.
        """,
        # -------------------------------
        """
        Now, I'd like to see what happens if the price of product-A is lower or equal to the price of product-B.
        """,
        # -------------------------------
        """
        Do the same, but now the price of product-A is strictly lower to the price of product-B.
        """,
        # -------------------------------
        """
        I would like the price of A to be between 0.5 and 1.5.
        """,
    ]
    USER_MESSAGES = [textwrap.dedent(message).strip() for message in USER_MESSAGES]

    driver = webdriver.Chrome()
    driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    driver.set_window_position(0, 0)  # Move window to the left
    driver.get("http://localhost:32123")
    time.sleep(3)

    chat_input = driver.find_element(
        By.XPATH,
        "/html/body/mesop-editor-app/mesop-editor/mesop-shell/mat-sidenav-container/mat-sidenav-content/component-renderer/component-renderer/component-renderer/component-renderer[2]/component-renderer[3]/component-renderer[1]/component-renderer/ng-component/textarea",
    )
    count_chat_bot_messages = 0

    for message in USER_MESSAGES:
        type_like_human(chat_input, message)
        press_enter(chat_input)
        wait_for_chatbot_answer(driver, count_chat_bot_messages)
        chatbot_messages = get_chatbot_messages(driver)
        count_chat_bot_messages = len(chatbot_messages)

        if "proceed" in chatbot_messages[-1].lower() and "?" in chatbot_messages[-1]:
            type_like_human(chat_input, "Yes please do.")
            press_enter(chat_input)
            wait_for_chatbot_answer(driver, count_chat_bot_messages)
            chatbot_messages = get_chatbot_messages(driver)
            count_chat_bot_messages = len(chatbot_messages)

    driver.quit()


if __name__ == "__main__":
    main()
