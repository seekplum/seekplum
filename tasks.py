# -*- coding: utf-8 -*-

from invoke import task


@task
def clean(ctx):
    """清除代码中无效文件
    """
    ctx.run("find . -name '*.pyc' -exec rm -f {} +", echo=True)
    ctx.run("find . -name '*.pyo' -exec rm -f {} +", echo=True)
    ctx.run("find . -name '*.log' -exec rm -f {} +", echo=True)
    ctx.run("find . -name '__pycache__' -exec rm -rf {} +", echo=True)
    ctx.run("find . -name 'htmlcov' -exec rm -rf {} +", echo=True)
    ctx.run("find . -name '.coverage*' -exec rm -rf {} +", echo=True)
    ctx.run("find . -name '.pytest_cache' -exec rm -rf {} +", echo=True)
    ctx.run("find . -name '.benchmarks' -exec rm -rf {} +", echo=True)
    ctx.run("find . -name '*.egg-info' -exec rm -rf {} +", echo=True)


@task(clean)
def check(ctx, job=4):
    """检查代码规范
    """
    ctx.run('find . -name "*.py" | '
            'xargs pylint --rcfile=.pylintrc -j %s --output-format parseable --disable=W0511,C0111,W0212' % job,
            echo=True)


@task
def lock(ctx):
    ctx.run('if [ -f "Pipfile.lock" ]; then pipenv lock -v --keep-outdated ; else pipenv lock ; fi', echo=False)
