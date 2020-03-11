# DynUpdate - DynUpdate Client

[![Build Status](https://travis-ci.org/Turgon37/DynDNSUpdate.svg?branch=master)](https://travis-ci.org/Turgon37/DynDNSUpdate)
[![codecov](https://codecov.io/gh/Turgon37/DynDNSUpdate/branch/master/graph/badge.svg)](https://codecov.io/gh/Turgon37/DynDNSUpdate)

A client script for DynDNS service.

This client is provided in two implementations, one in bash and the other one in python.

The recommanded version is python script, but the bash script is still available only for history purposes, it is not tested anymore.

## Usage

```bash
./dyndnsupdate.py --dyn-server https://www.api.com --dyn-hostname hostname.domain.com -u login -p pass
```

Please use the --help statement on each script to learn how to use them

## Installation

Just put these in a folder and run from cmd line

### Requirements per implementations:
  - for python version
    * python >= 3.4

  - for bash version
    * wget
