#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
线程池实现：
    https://www.cnblogs.com/zhang293/p/7954353.html
    http://www.cnblogs.com/hellojesson/p/6400415.html
"""
import time
import threading

number = 0
lock = threading.Lock()
r_lock = threading.RLock()


class MyThreadLock(threading.Thread):
    def run(self):
        global number
        time.sleep(1)
        if lock.acquire(1):
            number += 1
            msg = self.name + ' set number to ' + str(number)
            print msg
            lock.acquire()
            lock.release()
            lock.release()


class MyThreadRLock(threading.Thread):
    def run(self):
        global number
        time.sleep(1)
        if r_lock.acquire(1):
            number += 1
            msg = self.name + " number to " + str(number)
            print msg
            r_lock.acquire()
            r_lock.release()
            r_lock.release()


def lock_test():
    # 一个线程"迭代"请求同一个资源，直接就会造成死锁
    for i in range(5):
        t = MyThreadLock()
        t.start()


balance = 0


def change_it(n):
    # 先存后取，结果应该为0:
    global balance
    balance = balance + n
    balance = balance - n


def run_thread(n):
    for i in range(100000):
        # ========= 第一种方式 ===========
        # 先要获取锁:
        lock.acquire()
        try:
            # 锁只有一个，无论多少线程，同一时刻最多只有一个线程持有该锁
            change_it(n)
        finally:
            # 改完了一定要释放锁:
            lock.release()
        # # ========= 第二种方式 ===========
        # with threading.Lock():
        #     change_it(n)
        #     # with 语句会在这个代码块执行前自动获取锁，在执行结束后自动释放锁


if __name__ == '__main__':
    t1 = threading.Thread(target=run_thread, args=(50,))
    t2 = threading.Thread(target=run_thread, args=(8,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print balance
