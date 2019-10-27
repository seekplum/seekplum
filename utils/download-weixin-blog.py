# -*- coding: utf-8 -*-


from __future__ import print_function, unicode_literals

import codecs
import hashlib
import os
import random
import re
import string
import time
from functools import wraps, partial
from itertools import chain

import requests
import six.moves
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from jinja2 import FileSystemLoader, Environment


def get_md5(value):
    value = value.encode("utf-8")
    my_md5 = hashlib.md5()  # 获取一个MD5的加密算法对象
    my_md5.update(value)  # 得到MD5消息摘要
    digest = my_md5.hexdigest()  # 以16进制返回消息摘要，32位
    return digest


def random_string(length=5):
    """生成随机指定长度的字符串

    :return 随机字符串
    :rtype str
    """
    strings = string.lowercase + string.uppercase + string.digits
    return "".join([strings[random.randint(0, len(strings) - 1)] for _ in
                    six.moves.xrange(length)])


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


def statistical_service_time(func=None):
    """统计函数使用时间
    """

    if func is None:
        return partial(statistical_service_time)

    @wraps(func)
    def decorate(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        use_time = time.time() - start_time
        print("func [ %s ] use time [ %.3fs ]" % (func.__name__, use_time))
        return result

    return decorate


class DownloadWeixinBlog(object):
    def __init__(self, temp_dir):
        self._temp_dir = temp_dir
        self._thread_pool = ThreadPoolExecutor(max_workers=1)
        self._session = requests.session()
        self._timeout = 3
        self._pattern_img = re.compile(r"\?wx_fmt=[a-z]+")
        self._pattern_publish_time = re.compile(r',s="([\d\-]+)"')
        self._index_html_name = "index.html"

        self._create_directory()

    def _create_directory(self):
        """创建存放目录
        """
        if not os.path.exists(self._temp_dir):
            os.makedirs(self._temp_dir)

    @staticmethod
    def _get_title(soup):
        """获取文章标题

        :param soup soup对象
        :type soup BeautifulSoup

        :rtype basestring
        :return 文章标题
        """
        return soup.find("h2", attrs={"id": "activity-name"}).string.strip()

    @staticmethod
    def _gen_blog_name(title):
        title = get_md5(title)
        return "%s.html" % title

    @statistical_service_time
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

    def _get_context_publish_time_and_soup(self, url):
        """获取博客内容和发布时间

        :param url 博客对应的链接
        :type url basestring

        :returns 发布时间、文章标题、soup对象
        :rtype basestring、basestring、BeautifulSoup
        """
        try:
            response = self._session.get(url, timeout=self._timeout)
        except Exception as e:
            print("invalid url: %s" % url)
            print("request error: ", e)
            return

        context = response.text

        # 发布时间
        publish_time = self._pattern_publish_time.search(context).group(1)

        # 解析内容
        soup = BeautifulSoup(response.text, "html.parser")

        return publish_time, self._get_title(soup), soup

    @statistical_service_time
    def _render_catalog_and_write_html(self, catalogs):
        """生成目录索引，并写入HTML中

        :param catalogs 目录信息
        :type catalogs list(dict)
        :example catalogs [{
                    "publish_time": "2019-07-11",
                    "title": "测试",
                    "url": "a.html",
                }]
        """
        env = Environment(loader=FileSystemLoader("./"))
        template = env.get_template(self._index_html_name)
        content = template.render(catalogs=catalogs)
        with codecs.open(os.path.join(self._temp_dir, self._index_html_name),
                         "w+",
                         "utf-8") as f:
            f.write(content)

    @statistical_service_time
    def _get_info(self, urls):
        """获取所有的链接
        """
        futures = [
            self._thread_pool.submit(self._get_context_publish_time_and_soup,
                                     link) for link in urls]
        data = [future.result() for future in futures]

        # 过滤空数据
        data = filter(lambda x: x, data)

        # 增加随机文件名
        # data = map(lambda r: r + (random_string(),), data)

        # 按时间排序
        data = sorted(data, key=lambda x: x[0])
        return data

    def _update_blog_content_and_write_html(self, name, soup, head_blog,
                                            next_blog):
        """修改博客内容，插入上下一篇博客链接，并写入HTML文件中

        :param name 博客名字
        :type name basestring

        :param soup soup对象
        :type soup BeautifulSoup

        :param head_blog: 上一篇博客信息
        :type head_blog dict

        :param next_blog: 下一篇博客信息
        :type next_blog dict
        """
        # 注意: new_tag 获取的对象只能append或insert一次
        last_div = soup.find("div", attrs={"id": "js_content"})
        first_p = soup.new_tag("p", attrs={"style": "font-size: 20px"})
        last_p = list(last_div.children)[-8]
        last_p["style"] = "font-size: 20px; color: blue;"

        last_p.append(soup.new_tag("br"))
        kwargs = {
            "name": "a",
            "href": self._index_html_name,
            "attrs": {"style": "color: blue;"}
        }
        catalog_string = "回到目录"
        first_catalog = soup.new_tag(**kwargs)
        first_catalog.string = catalog_string
        first_p.append(first_catalog)

        last_catalog = soup.new_tag(**kwargs)
        last_catalog.string = catalog_string
        last_p.append(last_catalog)

        if head_blog:
            first_p.append(soup.new_tag("br"))
            last_p.append(soup.new_tag("br"))
            kwargs = {
                "name": "a",
                "href": self._gen_blog_name(head_blog["name"]),
                "attrs": {"style": "color: blue;"}
            }

            head_string = "上一篇: %s %s" % (
                head_blog["publish_time"],
                head_blog["title"])
            first_head = soup.new_tag(**kwargs)
            first_head.string = head_string
            first_p.append(first_head)

            last_head = soup.new_tag(**kwargs)
            last_head.string = head_string
            last_p.append(last_head)

        if next_blog:
            first_p.append(soup.new_tag("br"))
            last_p.append(soup.new_tag("br"))
            kwargs = {
                "name": "a",
                "href": self._gen_blog_name(next_blog["name"]),
                "attrs": {"style": "color: blue;"}
            }
            next_string = "下一篇: %s %s" % (
                next_blog["publish_time"],
                next_blog["title"])
            first_next = soup.new_tag(**kwargs)
            first_next.string = next_string
            first_p.append(first_next)

            last_next = soup.new_tag(**kwargs)
            last_next.string = next_string
            last_p.append(last_next)

        last_div.insert(0, first_p)
        # 删除script
        s = soup.find("script", attrs={"id": "moon_inline"})
        s.extract()
        context = soup.prettify()
        with codecs.open(
                os.path.join(self._temp_dir, self._gen_blog_name(name)), "w+",
                "utf-8") as f:
            # context = re.sub(self._pattern_img, "", context)
            context = context.replace("data-src", "src")
            context = context.replace("https://", "http://")
            f.write(context)

    def _write_blog(self, length, index, item, data):
        """写入博客内容
        """
        date_day = item[0]
        soup = item[2]
        publish_time = "%d. %s" % (index + 1, date_day)

        title_index = 1
        name_index = 1
        title = item[title_index]
        name = item[name_index]

        next_blog = {
            "title": data[index + 1][title_index],
            "name": data[index + 1][name_index],
            "publish_time": "%d.%s" % (index + 2, data[index + 1][0])
        } if index < length - 1 else None
        head_blog = {
            "title": data[index - 1][title_index],
            "name": data[index - 1][name_index],
            "publish_time": "%d.%s" % (index, data[index - 1][0])
        } if index > 0 else None

        self._update_blog_content_and_write_html(name, soup, head_blog,
                                                 next_blog)
        return {
            "publish_time": publish_time,
            "title": title,
            "url": self._gen_blog_name(name),
        }

    @statistical_service_time
    def _get_catalogs(self, data):
        """获取目录
        """
        length = len(data)
        print("Total Blog: %d" % length)
        futures = [
            self._thread_pool.submit(self._write_blog, length, index, item,
                                     data) for index, item in enumerate(data)]
        # 所有的目录
        catalogs = [future.result() for future in futures]
        return catalogs

    def collect(self, urls):
        """收集博客信息

        :param urls 页面对应的链接集合
        :type urls set
        """
        data = self._get_info(urls)
        catalogs = self._get_catalogs(data)

        self._render_catalog_and_write_html(catalogs)
        print("Done! Please run `open %s`" % os.path.join(self._temp_dir,
                                                          self._index_html_name))
        return


@statistical_service_time
def main():
    d = DownloadWeixinBlog("/tmp/html")
    urls = [
        "https://mp.weixin.qq.com/s/4kTtn_gLYQrX7JFlEJdsZg",  # 2017汇总
        "https://mp.weixin.qq.com/s/oFQHrCZvItgc8McrZSaovw",  # 2018汇总
        "https://mp.weixin.qq.com/s/Ok5SjqhiQkG5sLUPNY02Mw",  # 2019汇总
    ]
    blog_urls = map(d.parser, urls)
    blog_urls = set(list(chain.from_iterable(blog_urls)))
    d.collect(blog_urls)


if __name__ == '__main__':
    main()
