# -*- coding: utf-8 -*-
import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementNotVisibleException


class OAuth(object):
    def __init__(self, driver, actions, username, password):
        self._driver = driver
        self._actions = actions
        self._username = username
        self._password = password

    def login(self):
        try:
            self._open_login()
            self._open_iframe()
            self._switch_login_mode()
            self._input_auth()
            self._auth_code()
            self._submit_login()
        finally:
            # 等待后退出浏览器
            time.sleep(3)
            self._driver.quit()

    def _open_login(self):
        """打开登录页面"""
        oauth_url = ""
        self._driver.get(oauth_url)

    def _open_iframe(self):
        """登录页面使用了iframe,获取真实的登录页"""
        login_iframe = self._driver.find_element_by_id("J_loginIframe")
        # 获取登录url
        login_url = login_iframe.get_attribute("src")
        self._driver.get(login_url)

    def _switch_login_mode(self):
        """默认是扫码登录，切换成账号密码的登录"""
        try:
            self._driver.find_element_by_class_name("login-switch").click()
            # driver.find_element_by_class_name("J_Quick2Static").click()
        except ElementNotVisibleException:
            pass

    def _input_auth(self):
        """输入用户名密码"""
        self._driver.find_element_by_name("TPL_username").send_keys(self._username)
        self._driver.find_element_by_name("TPL_password").send_keys(self._password)

    def _auth_code(self):
        """滑动滑块"""
        # 等待滑块出现
        time.sleep(1)

        # 找到滑块
        source = self._driver.find_element_by_id("nc_1_n1z")
        # 执行滑动操作
        self._actions.drag_and_drop_by_offset(source, 293, 0).perform()
        # 滑动结束释放鼠标
        self._actions.move_to_element(source).release()

        # TODO: 滑块解锁一直失败
        self._driver.get_screenshot_as_file("error.png")

    def _submit_login(self):
        """点击登录按钮"""
        self._driver.find_element_by_id("J_SubmitStatic").click()


def get_options():
    options = Options()
    # options.add_argument("--headless")
    prefs = {
        "profile.managed_default_content_settings.images": 1
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--proxy-server=http://127.0.0.1:9000")
    options.add_argument("disable-infobars")
    options.add_argument("--no-sandbox")
    return options


def main():
    options = get_options()
    driver = webdriver.Chrome(options=options)
    actions = ActionChains(driver)
    username = ""
    password = ""
    o = OAuth(driver, actions, username, password)
    o.login()


if __name__ == "__main__":
    main()

