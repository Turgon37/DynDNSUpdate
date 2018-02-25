# -*- coding: utf8 -*-

import shlex
import subprocess


# command line test
def test_cmdline():
    """Get usage and help functions"""
    result = subprocess.Popen(shlex.split('./dyndnsupdate.py --help'), stdout=subprocess.PIPE)
    stdout, stderr = result.communicate()
    assert 'usage:' in stdout.decode()

    result = subprocess.Popen(shlex.split('./dyndnsupdate.py --version'), stdout=subprocess.PIPE)
    stdout, stderr = result.communicate()
    assert 'DynDNS client version' in stdout.decode()
