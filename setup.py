from setuptools import setup, find_packages

setup(
    name='aioapollo',
    version='0.0.1',
    description=(
        '纯异步的apollo客户端，支持实时和延迟的获取配置信息',
        'Pure asynchronous Apollo client to support real-time and delayed access to configuration information'
    ),
    long_description=open('README.rst', 'rb').read(),
    author='beincy',
    author_email='bianhui0524@sina.com',
    maintainer='卞辉(beincy)',
    maintainer_email='bianhui0524@sina.com',
    license='MIT',
    packages=['aioapollo'],
    platforms=["all"],
    url='https://github.com/beincy/aioapollo',
    install_requires=[
        'uvloop',
        'ujson',
        'aiohttp'
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)