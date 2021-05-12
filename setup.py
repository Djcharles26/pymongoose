import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pymongoose",
    version="0.1",
    author="Juan Carlos Lara",
    author_email="jlaraanaya@gmail.com",
    description="A pymongo helper with methods and classes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/djcharles26/pymongoose",
    packages=setuptools.find_packages(where="pymongoose"),
    package_dir={"":"src"},
    python_requires=">=3.8",

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent" 
    ]
)