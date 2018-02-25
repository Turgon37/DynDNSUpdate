# -*- coding: utf8 -*-

import shlex
import subprocess


# command line test
def test_cmdline():
    """Must produce an error is no url was given"""
    result = subprocess.Popen(shlex.split('./dyndnsupdate.py --help'), stdout=subprocess.PIPE)
    stdout, stderr = result.communicate()
    assert 'usage:' in stdout.decode()

    result = subprocess.Popen(shlex.split('./dyndnsupdate.py --version'), stdout=subprocess.PIPE)
    stdout, stderr = result.communicate()
    assert 'DynDNS client version' in stdout.decode()
