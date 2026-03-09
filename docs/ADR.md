# Architecture Decision Record (ADR)


This document captures important architecture decisions made along with their context and consequences.

---

## version 0.1.0

This is the version created to meet the code challenge spec and test with the provided sample data. There was a short time to build it, so its design and development are generally biased to limit the time spent by the developer. 

### Architecture

Each API is all in one file. It may make sense to break them up into separate files (asset vs. version or perhaps modify vs. query). This sort of refactoring is like a day 3-5 kind of task, just outside the scope of the challenge.

The Python API designed for maximum modularity and performance. The CLI/service are designed for redundancy. Specifically the CLI and service will ensure the asset exists when creating a new asset version, where the Python API does not.

Asset version status is not really used for much, but there is an example use of it in the "latest version" APIs. It would make sense to add it as a common flag for the list and get queries.

The list results are not sorted, which would be easier to read and would be useful for debugging in a real production environment.

There is no authorization.

### Code

Running the tests does not affect the "production" database. Passes `ruff` format and lint tests, `bandit` security tests, and `pytest --cov=src --cov-branch` reports 99% code coverage, all with default settings. The only code not covered by tests is infrastructure in the `cli` module.

My personal style is not to use classes just to group functions and avoid having to instantiate a class just to call a single member method to start a process. I try to defer creation of any resources until the time they're needed, as you can see with the `AssetRegistry` class initialization.

There are some hacks for development speed to that need real packaging or deployment to fix (like the path munging in the `cli` module). There is no packaging of any kind.

Some of the result data structures and log messages are sloppy and inconsistent since the spec was open-ended and time was short.

Not a lot of syntactic sugar. With a more relaxed development schedule it would be great to have bits and bobs that make the code smaller, more consistent, and easier to read.

No optimization or performance analysis of any kind has been done, so it may not be the most efficient code yet.
