# -*- coding: utf-8 -*-


from __future__ import print_function

import re
import codecs

from textwrap import dedent

import requests

from bs4 import BeautifulSoup


def check_is_valid_url(url):
    """检查是否为有效的url

    :param url 链接
    :type url basestring

    :rtype bool
    """
    url = url.strip()
    if not url:
        return False

    invalid_head = ("javascript:", "#")
    if url.startswith(invalid_head):
        return False

    return True


class DownloadWeixinBlog(object):
    def __init__(self):
        self._session = requests.session()
        self._timeout = 3
        self._pattern_img = re.compile(r"\?wx_fmt=[a-z]+")
        self._pattern_publish_time = re.compile(r',s="([\d\-]+)"')

    def parser(self, url):
        """解析页面中的链接

        :rtype set
        :return 返回当前页面中所有有效的链接
        """
        response = self._session.get(url, timeout=self._timeout)

        # 解析内容
        soup = BeautifulSoup(response.text, "html.parser")

        return {
            link.attrs.get("href", "")
            for link in soup.find_all("a")
            if check_is_valid_url(link.attrs.get("href", ""))
        }

    def download(self, url):
        """下载博客

        :param url 博客对应的链接
        :type url basestring
        """
        response = self._session.get(url, timeout=self._timeout)

        # 解析内容
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h2", attrs={"id": "activity-name"}).string.strip()

        last_div = soup.find("div", attrs={"id": "js_content"})
        p_tag = soup.new_tag("p", style="white-space: normal;line-height: 25.6px;text-align: center;")
        head_tag = soup.new_tag("a", href="https:www.baidu.com")
        head_tag.string = "上一篇: 内容为"
        p_tag.append(head_tag)
        br_tag = soup.new_tag("br")
        p_tag.append(br_tag)
        next_tag = soup.new_tag("a", href="https:www.baidu.com")
        next_tag.string = "下一篇: 内容为"
        p_tag.append(next_tag)

        last_div.append(p_tag)
        context = soup.prettify()
        # 发布时间
        publish_time = self._pattern_publish_time.search(context).group(1)
        with codecs.open("%s.html" % title, "w+", "utf-8") as f:
            context = re.sub(self._pattern_img, "", context)
            context = context.replace("data-src", "src")
            f.write(context)


def main():
    d = DownloadWeixinBlog()
    url = "https://mp.weixin.qq.com/s/4kTtn_gLYQrX7JFlEJdsZg"
    # map(d.download, d.parser(url))
    count = 0
    for link in d.parser(url):
        d.download(link)
        if count > 5:
            break
        count += 1


if __name__ == '__main__':
    main()
