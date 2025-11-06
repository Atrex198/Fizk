from setuptools import setup, find_packages

setup(
    name="zkp-evaluation",
    version="1.0.0",
    description="Zero-Knowledge Proof Techniques Performance Evaluation Framework",
    author="Research Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.10.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "plotly>=5.14.0",
        "scikit-learn>=1.3.0",
        "tqdm>=4.65.0",
        "loguru>=0.7.0",
        "memory-profiler>=0.61.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.1.0", "black", "flake8"],
        "jupyter": ["jupyter>=1.0.0", "ipywidgets>=8.0.0"],
    },
)
