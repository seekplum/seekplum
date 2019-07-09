# -*- coding: utf-8 -*-
"""
1.检查 cdc_ 是否存在

sudo perl -ne 'while(/cdc_/g){print "$&\n";}' /usr/local/bin/chromedriver

2.进行替换

sudo perl -pi -e 's/cdc_/dog_/g' /usr/local/bin/chromedriver

3.再次进行检查

sudo perl -ne 'while(/cdc_/g){print "$&\n";}' /usr/local/bin/chromedriver

"""
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
        oauth_url = ("https://oauth.taobao.com/authorize?state=&"
                     "redirect_uri=http://meizhe.meideng.net/user/login_verify?"
                     "view=web&response_type=code&client_id=12265875&from_site=meizhe&view=web")

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

            # if self._driver.find_element_by_id("J_QRCodeLogin").is_displayed():
            #     self._driver.find_element_by_id("J_Quick2Static").click()
        except ElementNotVisibleException:
            pass

    def _input_auth(self):
        """输入用户名密码"""
        self._driver.find_element_by_name("TPL_username").send_keys(self._username)
        self._driver.find_element_by_name("TPL_password").send_keys(self._password)

    def _check_lock_exist(self):
        """判断是否存在滑动验证
        """
        return self._driver.find_element_by_css_selector("#nc_1_wrapper") and \
               self._driver.find_element_by_id("nc_1_wrapper").is_displayed()

    def _auth_code(self, retry=3):
        """滑动滑块"""
        # 等待滑块出现
        time.sleep(1)

        if not self._check_lock_exist():
            return
        # 找到滑块
        source = self._driver.find_element_by_id("nc_1_n1z")
        # 执行滑动操作
        self._actions.drag_and_drop_by_offset(source, 293, 0).perform()
        time.sleep(0.5)
        # 滑动结束释放鼠标
        self._actions.move_to_element(source).release()

        # TODO: 滑块解锁一直失败
        time.sleep(1.5)

        # 截取登录失败截图
        self._driver.get_screenshot_as_file("error.png")

        if self._driver.find_element_by_css_selector(".errloading > span"):
            error_message_element = self._driver.find_element_by_css_selector(".errloading > span")
            error_message = error_message_element.text
            self._driver.execute_script("noCaptcha.reset(1)")
            if retry < 0:
                raise Exception(u"滑动验证失败, message = " + error_message)
            self._auth_code(retry - 1)

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
    username = "123456"
    password = "123456"
    o = OAuth(driver, actions, username, password)
    o.login()


if __name__ == "__main__":
    main()
