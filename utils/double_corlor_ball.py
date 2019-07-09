# -*- coding: utf-8 -*-


from __future__ import print_function

from collections import Counter
from itertools import chain

import requests

from bs4 import BeautifulSoup
from urlparse import urljoin


class DoubleColorBall(object):
    def __init__(self, basic_url):
        self._basic_url = basic_url
        self._session = requests.session()
        self._timeout = 3

    def _get_page(self):
        """获取总页数

        :rtype int
        :return 总页数
        """
        url = urljoin(self._basic_url, "list_1.html")
        response = self._session.get(url, timeout=self._timeout)

        # 解析内容
        soup = BeautifulSoup(response.text, "html.parser")

        # 获取页数信息
        total_page = int(soup.find('p', attrs={"class": "pg"}).find_all('strong')[0].text)
        return total_page

    def _get_lottery_info(self, page):
        """获取某一页的开奖信息
        """
        url = urljoin(self._basic_url, "list_%d.html" % page)
        response = self._session.get(url, timeout=self._timeout)
        soup = BeautifulSoup(response.text, "html.parser")
        if not soup.table:
            return

        table_rows = soup.table.find_all('tr')
        balls = []
        for row_num in range(2, len(table_rows) - 1):
            ball = []
            row_tds = table_rows[row_num].find_all('td')
            ems = row_tds[2].find_all('em')

            ball.append(row_tds[0].string)  # 开奖日期
            ball.append(row_tds[1].string)  # 双色球期数

            ball.append(ems[0].string)  # 红色球1
            ball.append(ems[1].string)  # 红色球2
            ball.append(ems[2].string)  # 红色球3
            ball.append(ems[3].string)  # 红色球4
            ball.append(ems[4].string)  # 红色球5
            ball.append(ems[5].string)  # 红色球6

            ball.append(ems[6].string)  # 蓝色球
            balls.append(ball)
        return balls

    def collect(self):
        """收集所有开奖信息
        """
        # total_page = self._get_page()
        total_page = 2
        all_lottery = []
        for page in xrange(1, total_page + 1):
            lottery = self._get_lottery_info(page)
            if not lottery:
                continue

            all_lottery.extend(lottery)
        return all_lottery

    def analysis(self):
        """对结果进行分析
        """
        lottery_info = self.collect()
        red_lottery = [item[2:8] for item in lottery_info]
        # red_balls = chain(*red_lottery)
        red_balls = chain.from_iterable(red_lottery)
        red_counter = Counter(red_balls)
        # 获取出现次数最多的两个红球
        top = red_counter.most_common(2)
        print(top)


def main():
    basic_url = "http://kaijiang.zhcw.com/zhcw/html/ssq/"

    d = DoubleColorBall(basic_url)
    d.analysis()


if __name__ == '__main__':
    main()
