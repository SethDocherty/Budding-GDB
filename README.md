# Budding GDB toolset

![header_pic](./images/header_pic.png)

### Description:

A data structure designed for report map creation utilizing a “pseudo” one-way replication system to keep 
a **non-SDE**, child geo-database (GDB) synced to the parent GDB in a disconnected environment.

### Toolset Overview

In order to keep a child GDB synced with a parent GDB, a set of python scripts (found [here](./bin)) have been created to:
  - Replicate features of interest from the parent GDB
  - Update attributes of the replicated features stored in a child GDB so they match the attributes of the parent feature.
  - Update tables stored in the child GDB with new features from a database query.
  




