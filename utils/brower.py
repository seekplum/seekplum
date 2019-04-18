#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
1. Python 版本2.7
2. 依赖谷歌浏览器
3. 依赖谷歌浏览器的驱动
"""

import time

from selenium import webdriver


class Email163(object):
    def __init__(self, username, password):
        self.username = username  # 163邮箱用户名
        self.password = password  # 163邮箱密码
        self.driver = webdriver.Chrome()  # 获取浏览器
        self.driver.maximize_window()  # 把浏览器窗口最大化
        self.load_time = 5  # 加载页面等待的秒数

    def _login(self):
        """登录邮箱
        """
        url = "http://mail.163.com/"
        iframe_name = "x-URS-iframe"
        # 打开页面
        self.driver.get(url)
        # 点击邮箱登录
        self.driver.find_element_by_id('lbNormal').click()
        time.sleep(1)
        # 切换到表单
        self.driver.switch_to.frame(iframe_name)
        # 输入用户名密码
        self.driver.find_element_by_name("email").send_keys(self.username)
        self.driver.find_element_by_name("password").send_keys(self.password)
        # 点击登录按钮
        self.driver.find_element_by_id('dologin').click()

        # 可能会出现验证码, 10 输入验证码的时间
        self.sleep_time(10)

        # curr_handler = driver.current_window_handle
        # 从iframe中退出回到主页面中
        self.driver.switch_to.default_content()

    @staticmethod
    def sleep_time(seconds=1):
        """休眠 `seconds` 秒后再继续操作

        :param seconds: int 等待的秒数 default=1
        """
        time.sleep(seconds)

    def _do_check_box(self, box_message=None):
        """检查邮件是否全部被删除了

        :param box_message: str 检查的xpath

        :rtype bool
        :return
            True: 还未删除干净
            False: 邮件已经删除干净
        """
        # 通过判断字符串在网页中不准确,字符串被隐藏掉了
        # html = self.driver.page_source
        # result = False
        # if message.decode("utf-8") in html:
        #     result = True
        if box_message is None:
            box_message = "/html/body/div[2]/div[1]/div[2]/header/div/div[1]/div/span[1]/span"
        result = False
        try:
            # 选中全选框
            self.driver.find_element_by_xpath(box_message).click()
            result = True
        except Exception as e:
            # 选择全选框操作失败了, 说明邮件都被删除了
            print("选中全选框失败: {}".format(e.message))
        return result

    def _click_delete_button(self):
        """点击删除按钮
        """
        self.driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/header/div[1]/div[2]/div").click()

    def _delete_inbox(self):
        """删除收件箱内的邮件

        检查全选框是否能选中
            能:
                执行删除操作,再次回到 重复上一步检查
            不能:
                认为该项中的邮件都被删除了,继续下一步
        """
        # 点击收件箱
        self.driver.find_element_by_xpath("/html/body/div[1]/nav/div[2]/ul/li[1]").click()

        self.sleep_time(self.load_time)
        while self._do_check_box():
            self.sleep_time()

            # 点击删除按钮
            self._click_delete_button()

            self.sleep_time()
        else:
            print("收件箱所有邮件都被删除了")

    def _delete_sent(self):
        """删除已发送的邮件

        检查全选框是否能选中
            能:
                执行删除操作,再次回到 重复上一步检查
            不能:
                认为该项中的邮件都被删除了,继续下一步
        """
        # 点击已发送
        self.driver.find_element_by_xpath("/html/body/div[1]/nav/div[2]/ul/li[6]").click()

        self.sleep_time(self.load_time)
        while self._do_check_box():
            self.sleep_time()

            # 点击删除按钮
            self._click_delete_button()

            self.sleep_time()
        else:
            print("已发送的所有邮件都被删除了")

    def _delete_deleted(self):
        """删除已删除中的邮件

        检查全选框是否能选中
            能:
                执行删除操作
                执行确认操作
                重复上一步检查
            不能:
                认为该项中的邮件都被删除了,继续下一步
        """
        # 点击已删除
        self.driver.find_element_by_xpath("/html/body/div[1]/nav/div[2]/ul/li[7]").click()

        self.sleep_time(self.load_time)
        while self._do_check_box():
            self.sleep_time()

            # 点击删除按钮
            self._click_delete_button()

            error_message = []
            # div数量不确定
            for i in range(3, 12):
                try:
                    # 确认删除
                    self.driver.find_element_by_xpath("/html/body/div[{}]/div[3]/div[2]/div[1]".format(i)).click()
                except Exception as e:
                    message = "{}: {}".format(i, e.message)
                    error_message.append(message)
                else:
                    if error_message:
                        print("尝试了 {} 次才成功, {}".format(len(error_message), "\t".join(error_message)))
                    else:
                        print("尝试一次就删除成功")
                    break

            self.sleep_time()
        else:
            print("已删除中的所有邮件都被删除了")

    def _run(self):
        """执行删除的业务逻辑

        1. 登录
        2. 删除收件箱中的邮件
        3. 删除已发送中的邮件
        4. 删除已删除中的邮件
        """
        self._login()

        # 登录成功后等待页面加载完成
        self.sleep_time(self.load_time)

        self._delete_inbox()
        self._delete_sent()
        self._delete_deleted()

    def run(self):
        try:
            self._run()
        except Exception as e:
            print("执行操作发生了错误: {}".format(e.message))
        finally:
            self.driver.close()
            self.driver.quit()


def main():
    username = "xxx"  # 163邮箱用户名
    password = ""  # 163邮箱密码
    manager = Email163(username, password)
    manager.run()


if __name__ == '__main__':
    main()
