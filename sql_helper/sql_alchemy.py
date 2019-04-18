# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pip instaall MySQL-python失败，安装依赖
sudo apt-get install libmysqlclient-dev



mysql备份
mysqldump -h127.0.0.1  -P3306 -uroot -proot test > hhhhh.sql
mysql恢复，自己创建数据库test,切换到tests数据库
create database test;
use test;
source /home/hjd/sql/hhhhh.sql
mysql恢复，自己创建数据库test
mysql -h127.0.0.1  -P3306 -uroot -proot test < hhhhh.sql
"""
import settings
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData

Base = declarative_base()


class Address(Base):
    """电子邮件表"""
    __tablename__ = 'address'

    # id = Column(Integer, primary_key=True)
    email = Column(String(20), nullable=False, primary_key=True)
    name = Column(String(10), ForeignKey('users.name'))
    user_id = Column(String(20))

    # user = relationship("User", back_populates="address")

    def __repr__(self):
        return "<Address(email='%s')>" % self.email

    @classmethod
    def drop_table(cls):
        cls.__table__.drop(engine)
        # table_name = cls.__table__.name
        # table = metadata.tables[table_name]
        # metadata.drop_all(tables=[table])

    @classmethod
    def create_table(cls):
        metadata.create_all(tables=[Address.__table__])


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    # id = Column(Integer)
    name = Column(String(10), primary_key=True)
    fullname = Column(String(20))
    password = Column(String(20))

    # address = relationship("Address", order_by=Address.id, back_populates="user")

    @classmethod
    def drop_table(cls):
        cls.__table__.drop(engine)

    @classmethod
    def create_table(cls):
        metadata.create_all(tables=[User.__table__])

    def __repr__(self):
        return "<User(name='%s', fullname='%s', password='%s')>" % (self.name, self.fullname, self.password)


# echo=True
engine = create_engine('mysql+mysqldb://{username}:{password}@{host}:{port}/{db_name}'.format(
    **settings.db["mysql"]),
    pool_size=20,
    pool_recycle=3600,
    connect_args={"use_unicode": True, "charset": "utf8"})
Session = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)
metadata = MetaData(bind=engine)
session = Session()  # 先使用工程类来创建一个session


def insert():
    """ 插入数据 """

    def insert_address():
        ed_address = Address(email='111@qq.com', user_id=1, name='B')
        session.add(ed_address)
        # 同时创建多个
        session.add_all([
            Address(email='222@qq.com', user_id=4, name='D'),
            Address(email='333@qq.com', user_id=3, name='C'),
            Address(email='444@qq.com', user_id=2, name='A')
        ])
        # 提交事务
        session.commit()

    def insert_user():
        ed_user = User(name='A', fullname='Ed Jones', password='edspassword')
        session.add(ed_user)
        # 同时创建多个
        session.add_all([
            User(name='B', fullname='Wendy Williams', password='foobar'),
            User(name='C', fullname='Mary Contrary', password='xxg527'),
            User(name='D', fullname='Flinstone', password='blah'),
            User(name='E', fullname='Fred', password='blah'),
            User(name='F', fullname='Williams', password='blah'),
            User(name='G', fullname='Wendy', password='blah'),
            User(name='H', fullname='Jones', password='blah')
        ])
        # 提交事务
        session.commit()

    insert_user()
    insert_address()


def query():
    """ 查询 """
    for user in session.query(User).order_by(User.name):
        print "name:", user.name, "\nfullname", user.fullname

    # 使用filter_by过滤
    for name in session.query(User.name).filter_by(fullname='Mary Contrary'):
        print "filter name:", name

    # 使用sqlalchemy的SQL表达式语法过滤，可以使用python语句
    for name in session.query(User.name).filter(User.fullname == 'Mary Contrary'):
        print "SQL name", name
    # label:重命名功能
    label = session.query(User.fullname.label('new_name')).first()
    print "label: %s" % label.new_name  # 用new_name 代替fullname
    # in_
    in_ = session.query(User).filter(User.name.in_(['A', 'fakeuser'])).first()
    print "in_: %s" % in_.name
    result = session.query(User).filter(User.fullname == 'Mary Contrary').one()
    print '\n\n\n查询结果', type(result), result, result.name, '\n\n\n'

    # 多表连接查询
    name_email = session.query(User.name, User.password, Address.email).filter(User.name == Address.name).all()
    for item in name_email:
        print "name: %s, password: %s, email: %s" % (item.name, item.password, item.email)
    fullname_email = session.query(User.name, User.fullname, Address.email).join(
        (Address, User.name == Address.name)).all()
    for item in fullname_email:
        print "name: %s, fullname: %s, email: %s" % (item.name, item.fullname, item.email)


def create():
    """ 创表 """
    Base.metadata.create_all(engine)


def drop():
    """ 删除表 """
    Address.drop_table()
    User.drop_table()


def del_delete():
    session.query(User).filter(User.id == 1).delete()
    session.commit()


def update():
    """ 修改 """
    session.query(User).filter(User.name == 'ed').update({User.name: 'ABC'})
    session.commit()  # commit: 把内存里面的东西直接写入，可以提供查询了；
    # session.flush()  # flush: 预提交，等于提交到数据库内存，还未写入数据库文件；可以 rollback 回滚


if __name__ == '__main__':
    query()
