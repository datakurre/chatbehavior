from setuptools import setup, find_packages

setup(
    name="chatbehavior",
    version="1.0.0",
    description="Proof-of-concept AMQP based chat behavior for Dexterity",
    long_description=(open("README.rst").read() + "\n" +
                      open("CHANGES.txt").read()),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Programming Language :: Python",
    ],
    keywords="",
    author="Asko Soukka",
    author_email="asko.soukka@iki.fi",
    url="https://github.com/datakurre/chatbehavior/",
    license="GPL",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "five.grok",
        "plone.app.dexterity",
        "plone.app.referenceablebehavior",
        "zope.index",
        "simplejson",
        "collective.zamqp",
    ],
    extras_require={"test": [
        "plone.app.testing",
    ]},
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """
)
