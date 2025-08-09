from setuptools import setup


def read_long_description() -> str:
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "Interactive Help Desk ticket system CLI using data structures."


setup(
    name="interactive-helpdesk-cli",
    version="0.1.0",
    description="Interactive Help Desk ticket system CLI using data structures",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author="Prashidha",
    license="MIT",
    url="https://example.com/interactive-helpdesk-cli",
    project_urls={
        "Source": "https://example.com/interactive-helpdesk-cli",
    },
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0,<9.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Utilities",
    ],
    # We ship individual modules (flat files), not a package directory
    py_modules=["helpdesk", "LinkedList", "Stack", "ticket"],
    entry_points={
        "console_scripts": [
            "helpdesk=helpdesk:cli",
        ]
    },
)

