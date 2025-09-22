from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="system-diagnostics-mcp",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Comprehensive system monitoring and diagnostics MCP server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/system-diagnostics-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=0.9.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "windows": ["wmi>=1.5.1", "pywin32>=306"],
        "dev": ["pytest>=7.4.0", "pytest-asyncio>=0.21.0", "black>=23.0.0", "mypy>=1.5.0"],
    },
    entry_points={
        "console_scripts": [
            "system-diagnostics-mcp=system_diagnostics_mcp.server:main",
        ],
    },
)