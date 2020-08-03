from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='flatbush',
      version='1.1.0',
      description='flatbush spatial index',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/bmharper/flatbush-python',
      author='Ben Harper',
      author_email='rogojin@gmail.com',
      license='MIT',
      packages=['flatbush'],
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ],
      python_requires='>=3.6')