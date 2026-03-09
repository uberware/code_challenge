# LAIKA Pipeline Engineering Take-Home Challenge

## Implementation Nodes

When building production systems, I follow these general steps:

1. Make it work
2. Make it work well
3. Make it work fast

This code is deeply in step 1. It accomplishes the goals set out in the challenge with production quality code and tests, but may not be very well suited to actual production. Once it was fully fleshed out with the basic features and ready to start production testing, step 2 work would be polishing the architecture and usage patterns as needed. Once that was complete, step 3 would be to look for bottlenecks and performance improvements.

All API, CLI, and microservice endpoints from the challenge spec are implemented. I added a "get latest version" feature as well.

For more information see the [Architectural Design Record](ADR.md).

## Original Request

**Welcome!**

This challenge is designed to demonstrate your ability to write clean, maintainable, well-structured, and well-tested code.

This is **not** a timed exam. Feel free to take breaks and approach this as you would real production code. Typical completion time: **~4–6 hours**, including tests.

## ✅ Challenge Goal

You are tasked with building a small **Asset Validation & Registration Service** — a lightweight system that can:

1. Load asset metadata from a sample JSON file. 
   - Keep in mind, we will stress test your app with erroneous and large datasets. It would be a good idea to augment the sample set to ensure your implementation is durable.
2. Validate assets using an extensible validation pipeline
3. Store the validated assets in a persistence layer
4. Expose a Python API for the supplied CLI app to consume
5. Include unit tests

## ✅ Functional Requirements

### Asset Data Model

Your data should be validated against the following asset data model. What we’re looking for here is a clear extensible representation of an asset, versions of an asset, and their properties.  

Each asset has:

Asset:
| Field | Type | Notes |
| ------- | ------ | ------- |
| name | string | required |
| type | enum | character, prop, set, environment, vehicle, dressing, fx |

Asset Version:
| Field | Type | Notes |
| ------- | ------ | ------- |
| asset | foreign key | reference to the asset this version represents |
| department | string | required: ex. modeling, texturing, rigging, animation, cfx, fx |
| version | integer | ≥ 1 and follows a sequential order |
| status | enum | active, inactive |

- Asset uniqueness is described by its (name and type)
   - We do not allow multiple assets with the same name+type, but same name+different type or different name+same type are both fine 
- Each Asset should have at least 1 version associated with it and no duplicate versions 
   - Versions should also increment linearly by integer
- Asset version uniqueness is described by the (asset + department + version)
   - You may have `(hero+character)+animation+v1` and `(hero+character)+cfx+v1`, but not two `(hero+character)+animation+v1` entries

---

### Validation Pipeline

Now that we know the rules, the next task is to create your validation logic. There are a few ways to go about this, but we’ll leave it up to you to decide what the best approach should be. Some things to keep in mind are extensibility and composability. 

Your validation system should obey the following rules:
- Name is required
- Type is a known valid value
- Department is required
- Version is an integer 1 or greater and follows a sequential order, 1, 2, 3, ...
- Status is a known valid value

Invalid data should not halt execution. Your solution should detect and handle invalid entries gracefully (e.g., via validation, skipping, or logging), while continuing to process all valid entries.

---

### Storage

Now that our data is squeaky clean and valid, we need someplace to store it. Please create a persistence layer in the application, this can be a full on DB or a file backed solution. The persistence layer should be abstracted and portable, different services should be able to easily utilize it. 

Choose one of the following:
- ✅ A lightweight DB such as SQLite
- ✅ JSON file storage with storage abstraction
- ✅ In-memory DB with a storage layer abstraction

---
### Creating the package/application

Now that we know the parts that are necessary, it’s time to allow users to interact with your system. 

The main thing we want to see is a Python API, build a clean API that can be consumed by the CLI. This API will ingest, validate, and store assets and asset versions; users should then be able to retrieve the validated asset and version information. 

For bonus points, create a REST API. 

**Python API**
```python
# Example interface:

# Load sample data
load_assets(file.json)

# add an asset
add_asset(asset_name, asset_type)

# list all assets
list_assets()

# retrieve asset by name
get_asset(asset_name, asset_type)

# add an asset version
add_asset_version(asset_data, version_data)

# list versions of an asset
list_asset_versions(asset_name, asset_type)

# retrieve asset version by version number
get_asset_version(asset_name, asset_type, version_num)
```

**CLI**
```sh
# Example commands:

# load assets
load <asset_data.json>

# add an asset
add <asset_name> <asset_type>

# get an asset
get <asset_name> <asset_type>

# list all assets
list

# add an asset version
versions add <asset_name> <asset_type> <department> <version_num> <status>

# get an asset version
versions get <asset_name> <asset_type> <department> <version_num>

# list all asset versions
versions list <asset_name> <asset_type>
```

**Bonus Points: REST API**

```sh
# Example endpoints:

# Load sample data
POST /assets/load

# add an asset
POST /assets

# add an asset version
POST /assets/versions

# list all assets
GET /assets

# retrieve asset by name
GET /assets?asset={asset_name}&type={asset_type}

# list all versions of an asset
GET /assets/versions?asset={asset_name}&type={asset_type}

# retrieve an asset version
GET /assets/versions?asset={asset_name}&type={asset_type}&version={asset_version}
```
_Frameworks allowed: Flask, FastAPI, Django, or similar._

---

### Tests

Testing is an important part of any application development cycle. Make sure to include robust tests that cover any business logic such as validation and persistence. You should also think about possible edge cases that may arise. We’re looking for unit tests, so sticking with pytest or unittest is a good path.

## ✅ Deliverables

Please create a **git repository**, complete with **detailed commits**. Once you’re happy with the application, you can either send us a link to your GitHub repo or a compressed file with your codebase as a zip/tar file. 

Please include:
- ✅ Source code
- ✅ Git history
- ✅ Instructions to run and test
- ✅ Brief technical overview (design choices, architecture decisions, future improvements)

_Docker is welcome, but not required._

## ✅ Evaluation Criteria

When it comes time for us to review your code challenge, we’ll be looking at a few key aspects. 

| Category | What we look for |
| ------- | ------ |
| Code readability | clean, logical structure, maintainable |
| Architecture | clear separation of concerns, modular design |
| Extensibility | easy to add new validation rules or new storage types |
| Testing | meaningful unit test coverage |
| Documentation | clear README and code comments |
| Error handling | helpful messages, graceful failures |
| Performance & efficiency | sensible approaches, no over-engineering |

## ✅ Stretch Ideas (Optional)

Not required, but impressive if included:

- Configurable validation rules (via JSON/YAML)
- Logging 
- Docker environment
- CI config (GitHub Actions, etc.)

<br>

---

<br>

That’s the entire challenge. Build as you would build production-quality code. 

If you have any questions or hit blockers during the challenge, feel free to reach out.

Good luck — we can’t wait to see your approach!
