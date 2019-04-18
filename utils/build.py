#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pybuilder.core import use_plugin, init, task, depends

version = '6.0.0'

use_plugin('python.install_dependencies')


default_task = ['init_environment']


@init
def initialize(project):
    project.set_property('install_dependencies_index_url', "https://mirrors.ustc.edu.cn/pypi/web/simple")
    project.build_depends_on("pipenv", version='==11.0.2')


@task
@depends('install_build_dependencies')
def init_environment(logger):
    logger.info("Init environment")
    import subprocess
    logger.debug("Running cmd: pipenv install --skip-lock")
    subprocess.check_call(['PIPENV_VENV_IN_PROJECT=1 pipenv install --skip-lock'], shell=True)
    logger.info("Installing pyconcrete")
    logger.debug("Running cmd: pipenv run pip install --egg pyconcrete --install-option='--passphrase=******'")
    subprocess.check_call(
        ['pipenv run pip install pyconcrete --egg --install-option="--passphrase=password"'], shell=True
    )


@task
@depends('init_environment')
def install_cx_oracle_client(logger):
    import subprocess, os

    logger.info("Creating directory: .venv/packages/oracle")
    oracle_client_path = '.venv/packages/oracle'
    subprocess.check_call(['mkdir -p {}'.format(oracle_client_path)], shell=True)
    logger.info("Decompressing oracle instance client")
    subprocess.check_call(['tar xvzf packages/instantclient_12_2.tar.gz -C {}'.format(oracle_client_path)], shell=True)

    path = os.path.join(os.path.join(os.getcwd(), oracle_client_path), 'instantclient_12_2')
    path_value = "export LD_LIBRARY_PATH={}:$LD_LIBRARY_PATH".format(path)
    logger.info("Setting environment: {}".format(path_value))
    subprocess.check_call(['echo {} >> .venv/bin/activate'.format(path_value)], shell=True)
