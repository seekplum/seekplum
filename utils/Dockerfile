FROM centos:6.6

RUN yum -y update && \
    yum groupinstall -y development && \
    yum install -y \
    bzip2-devel \
    git \
    hostname \
    openssl \
    openssl-devel \
    sqlite-devel \
    sudo \
    tar \
    wget \
    zlib-dev \
    mysql-devel \
    libaio

# Install python2.7.6
RUN cd /tmp && \
    wget https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz && \
    tar xvfz Python-2.7.6.tgz && \
    cd Python-2.7.6 && \
    ./configure --prefix=/usr/local && \
    make && \
    make install


# Install setuptools + pip + virtualenv
RUN cd /tmp && \
    curl https://bootstrap.pypa.io/get-pip.py | python - && \
    pip install virtualenv
