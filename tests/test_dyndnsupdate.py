# -*- coding: utf8 -*-

import http.client
import logging
import shlex
import shutil
import socket
import ssl
import subprocess
from unittest.mock import patch, Mock

from .mocks.connexionmock import createHTTPConnectionMock, createHTTPSConnectionMock

import dyndnsupdate


# URL settings
def test_without_setting():
    """Must produce an error is no url was given"""
    program = dyndnsupdate.DynDNSUpdate()
    assert program.main() == 3

@patch('http.client.HTTPConnection', createHTTPConnectionMock())
def test_with_valid_settings():
    """Must produce an error is bad urls were given"""
    shutil.rmtree('tmp', ignore_errors=True)

    program = dyndnsupdate.DynDNSUpdate()
    program.configure(dyndns_myip='1.1.1.1', server_url='www.api.com/', dyndns_hostname=['mydyndnshostname.com'])
    assert program.main() == 0
