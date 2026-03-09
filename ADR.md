Architectural Design Record

# version 0.1.0

- The api is all in one place - if it gets much bigger, it would make sense to break it up into separate files (perhaps add/modify vs. query)
- My personal style is not to use classes just to group functions and avoid having to instantiate a class just to call a single member method to start a process
- There are some hacks for development speed to that need real design to fix (like the path munging in the `cli` module)
- The Python API designed for maximum modularity and performance. The CLI/service are designed for redundancy. (specifically they create both the asset and asset version, where the Python API does not.)
- Tests do not use the "production" database. Passes `ruff` format and lint tests, `bandit` security tests, and `pytest --cov=src --cov-branch` reports 99% code coverage
- Some of the result data structures and log messages are sloppy and inconsistent since the spec was open-ended and time was short
- The list results are not sorted, which is more of an aesthetic issue (it would be useful for debugging in a real production environment)
- Asset version status is not really used for much, but did a little actual use of it in the "latest version" APIs. 
- Not a lot of syntactic sugar. With a more relaxed development schedule it would be great to have bits and bobs that make the code smaller, more consistent, and easier to read.
- No optimization or performance analysis of any kind has been done, so it may not be the most efficient code yet.
