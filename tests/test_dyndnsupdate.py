# -*- coding: utf8 -*-

import http.client
import logging
import shlex
import shutil
import socket
import ssl
import subprocess
from unittest.mock import patch, Mock, call

from .mocks.connexionmock import createHTTPConnectionMock, createHTTPSConnectionMock

import dyndnsupdate


# URL settings
def test_without_setting():
    """Must produce an error is no url was given"""
    program = dyndnsupdate.DynDNSUpdate()
    assert program.main() == 3

@patch('http.client.HTTPConnection', createHTTPConnectionMock())
@patch('http.client.HTTPSConnection', createHTTPSConnectionMock())
def test_with_valid_settings():
    """Must produce an error is bad urls were given"""
    program = dyndnsupdate.DynDNSUpdate()
    assert program.configure(dyndns_myip='1.1.1.1', server_url='www.api.com:81/',
                                verbose=-1,
                                dyndns_hostname=['mydyndnshostname.com']) == True
    assert program.main() == 0

    program = dyndnsupdate.DynDNSUpdate()
    assert program.configure(dyndns_myip='1.1.1.1',
                                verbose=1,
                                server_url='https://www.api.com/',
                                dyndns_hostname=['mydyndnshostname.com']) == True
    assert program.main() == 0


def test_with_invalid_url():
    """Must produce an error is bad urls were given"""
    program = dyndnsupdate.DynDNSUpdate()
    assert program.configure(server_url='ftp://lmdaz') == False
    assert program.main() == 3

def test_with_missing_settings():
    """Must produce an error is there is any missing setting"""

    program = dyndnsupdate.DynDNSUpdate()
    assert program.configure(server_url='http://lmdaz') == True
    assert program.main() == 3

@patch('http.client.HTTPConnection', createHTTPConnectionMock())
def test_with_http_auth():
    """Correct usage of HTTP basic auth"""

    program = dyndnsupdate.DynDNSUpdate()
    assert program.configure(dyndns_myip='1.1.1.1',
                            server_url='http://www.api.com/',
                            dyndns_hostname=['mydyndnshostname.com'],
                            server_username='user', server_password='pass') == True
    assert program.main() == 0
    c1 = call().request('GET',
    'http://www.api.com/nic/update?system=dyndns&hostname=mydyndnshostname.com&myip=1.1.1.1&wildcard=NOCHG&mx=&backmx=NOCHG&offline=NOCHG&url=', headers={'User-Agent': 'dyndns-update/'+dyndnsupdate.__version__, 'Authorization': 'Basic dXNlcjpwYXNz'})
    http.client.HTTPConnection.assert_has_calls([c1])

@patch('http.client.HTTPSConnection', createHTTPSConnectionMock('0.0.0.0'))
@patch('ssl._create_unverified_context', return_value=Mock(spec=ssl.SSLContext))
def test_insecure_https_address_from_url(ssl_context_mock, capsys):
    """Use insecure SSL transaction"""
    # https
    program = dyndnsupdate.DynDNSUpdate()
    assert program.configure(dyndns_myip='1.1.1.1',
                            server_url='https://www.api.com/',
                            tls_insecure=True,
                            dyndns_hostname=['mydyndnshostname.com'],
                            server_username='user', server_password='pass') == True
    assert program.main() == 0

    ssl._create_unverified_context.assert_called_once_with()
