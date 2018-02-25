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

def test_cmdline_exit_with_2():
    """Feed a bad url must produce a 2 return code"""
    result = subprocess.Popen(shlex.split('./dyndnsupdate.py --dyn-address 1.1.1.1 --dyn-server ftp://www.ovh.com --dyn-hostname d'), stdout=subprocess.PIPE)
    stdout, stderr = result.communicate()
    assert result.returncode == 2
