#!/usr/bin/env python3
# -*- coding: utf8 -*-

# This file is a part of DynDNSUpdate
#
# Copyright (c) 2014-2018 Pierre GINDRAUD
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""DynDNSUpdate program

A simple DynDNS client
"""

# System imports
import argparse
from base64 import b64encode
import http.client
import logging
import re
import socket
import sys
import urllib

# Global project declarations
__version__ = '2.0.0'


class DynDNSUpdate(object):
    """An instance of a dyn client

    This class represent a instance of a dyn dns client until it make
    his http query to update a remote dns server entry
    """

    # define the http protocol string
    REG_E_PROTO = 'https?'

    # match a exact ipv4 address
    REG_E_IPV4 = '(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])'

    # according to RFC 1123 define an hostname
    REG_E_HOST = '(?:(?:[a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])'

    # match the exact value of a port number
    REG_E_PORT = '(?:[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])'

    # match a resource's path
    REG_E_PATH = '/(?:(?:[a-zA-Z0-9-_~.%]+/?)*)?'

    # match some http parameters
    REG_E_QUERY = '\?(?:&?[a-zA-Z0-9-_~.%]+=?[a-zA-Z0-9-_~.%]*)+'

    # an URL is defined by :
    # PROTO+AUTH+IP|HOST+PORT+PATH+QUERY
    REG_E_URL = ('^(?P<url>(?:(?P<proto>' + REG_E_PROTO + ')://)?' +  # HTTP
               '(?P<host>' + REG_E_IPV4 + '|' + REG_E_HOST + ')' +  # HOST or IP
               '(?P<port>:' + REG_E_PORT + ')?' +  # PORT
               '(?P<path>' + REG_E_PATH + ')?' +  # PATH
               ')$')

    # an ip address is version 4
    REG_E_IP = '^(?P<ipv4>' + REG_E_IPV4 + ')$'  # IP matching

    # re match object
    RE_URL = re.compile(REG_E_URL)
    RE_IP = re.compile(REG_E_IP)

    def __init__(self):
        """Constructor : Build an launcher for dynupdate
        """
        # Network required
        self.__server_url = None
        self.__server_api_url = '/nic/update'
        self.__server_username = None
        self.__server_password = None
        self.__tls_insecure = False
        # The HTTP timeout
        self.__timeout = 5

        # init logger
        self.__logger = logging.getLogger('dynupdate')
        self.__logger.setLevel(logging.DEBUG)

        # remove all previously defined handlers
        for handler in self.__logger.handlers:
            self.__logger.removeHandler(handler)
        # default format for all handlers
        out_formatter = logging.Formatter("%(levelname)s [%(name)s] : %(message)s")
        # register stdout handler
        self.__logger_stdout = logging.StreamHandler(sys.stdout)
        self.__logger_stdout.setFormatter(out_formatter)
        self.__logger_stdout.setLevel(logging.INFO)
        self.__logger.addHandler(self.__logger_stdout)
        # register stderr handler
        self.__logger_stderr = logging.StreamHandler(sys.stderr)
        self.__logger_stderr.setFormatter(out_formatter)
        self.__logger_stderr.setLevel(logging.CRITICAL+1)
        self.__logger.addHandler(self.__logger_stderr)

        # DYNDNS protocol
        # for detail see https://help.dyn.com/remote-access-api/perform-update/
        self.__fields = dict()

        # Identify update type
        # "dyndns", "statdns"
        self.__fields['system'] = 'dyndns'

        # A comma separated list of host to update (max 20)
        self.__fields['hostname'] = ''

        # The IP address to set.
        # If not set or incorrect the server will choose himself an IP
        self.__fields['myip'] = ''

        # Parameter enables or disables wildcards for this host.
        # Values : "ON","NOCHG","OFF"
        self.__fields['wildcard'] = 'NOCHG'

        # Specify an eMail eXchanger
        self.__fields['mx'] = ''

        # Requests the MX in the previous parameter to be set up as a backup MX
        # by listing the host itself as an MX with a lower preference value.
        # Values : "ON","NOCHG","OFF"
        self.__fields['backmx'] = 'NOCHG'

        # Set the hostname to offline mode
        # "YES" turn on offline redirect for host
        # "NOCHG" no make change
        self.__fields['offline'] = 'NOCHG'

        # No already use
        self.__fields['url'] = ''


    def configure(self, **options):
        """Parse input main program options (restrict to program strict execution)

        @param[dict] options : array of option key => value
        """
        if 'verbose' in options:
            if options['verbose'] < 0:
                self.__logger_stdout.setLevel(logging.CRITICAL + 1)
            else:
                self.__logger_stdout.setLevel(logging.INFO - options['verbose']*10)
        self.__logger.debug('configured with args %s', options)
        if 'errors_to_stderr' in options and options['errors_to_stderr']:
            self.__logger_stderr.setLevel(logging.ERROR)
        # disable SSL certificate verification
        if 'tls_insecure' in options and options['tls_insecure']:
            self.__tls_insecure = True
        # http timeout
        if 'timeout' in options and options['timeout']:
            self.__timeout = options['timeout']
        # http settings
        if 'server_url' in options and options['server_url']:
            match = DynDNSUpdate.RE_URL.match(options['server_url'])
            if match:
                self.__server_url = match.groupdict()
            else:
                self.__logger.error('given server url "%s" is incorrect', options['server_url'])
                return False
        if 'server_api_url' in options and options['server_api_url']:
            self.__server_api_url = options['server_api_url']
        if 'server_username' in options and options['server_username']:
            self.__server_username = options['server_username']
        if 'server_password' in options and options['server_password']:
            self.__server_password = options['server_password']

        # dyn dns parsing
        if 'dyndns_myip' in options and options['dyndns_myip']:
            match = DynDNSUpdate.RE_IP.match(options['dyndns_myip'])
            if match:
                self.__fields['myip'] = match.group('ipv4')
            else:
                self.__logger.error('given ip address "%s" is incorrect', options['dyndns_myip'])
                return False
        if 'dyndns_hostname' in options and options['dyndns_hostname']:
            hostnames = options['dyndns_hostname']
            if isinstance(hostnames, list):
                hostnames = ','.join(hostnames)
            self.__fields['hostname'] = hostnames

        if 'dyndns_wildcard' in options and options['dyndns_wildcard']:
            if options['dyndns_wildcard'] in ['ON', 'OFF', 'NOCHG']:
                self.__logger.warning('Deprecated: Flag wildcard can be currently ignored')
                self.__fields['wildcard'] = options['dyndns_wildcard']
            else:
                self.__logger.error('Incorrect value for dyndns_wildcard option')
                return False
        return True

              #
              # if opt[0] == '--backmx':
              #   self.__fields['backmx'] = 'YES'
              # if opt[0] == '--no-backmx':
              #   self.__fields['backmx'] = 'NO'
              # if opt[0] == '--offline':
              #   self.__fields['offline'] = 'YES'
              # if opt[0] == '--static':
              #   self.__fields['system'] = 'statdns'
              # if opt[0] == '--url':
              #   self.__fields['url'] = opt[1]

    def main(self):
        """Entry point of the program
        """
        if not self.__server_url:
            self.__logger.error('Missing required setting "server_url" in configure()')
            return 3
        for required_field in ['myip', 'hostname']:
            if not self.__fields[required_field]:
                self.__logger.error('Missing required setting "%s" in configure()', required_field)
                return 3

        self.__logger.debug('debug: config fields ' + str(self.__fields))
        return int(not self.__query())

    def __query(self):
        """Forge and send the HTTP GET query

        @return[integer] : True if query success
                          False otherwise
        """
        url_parts = self.__server_url
        host = url_parts['host']
        port = None
        if url_parts['port']:
            port = url_parts['port']

        # PROTOCOL
        if not url_parts['proto'] or url_parts['proto'] == 'http':
            self.__logger.debug('-> protocol HTTP')
            if port is None:
                port = http.client.HTTP_PORT
            conn = http.client.HTTPConnection(host, port, timeout=self.__timeout)
        elif url_parts['proto'] == 'https':
            self.__logger.debug('-> protocol HTTPs')
            if port is None:
                port = http.client.HTTPS_PORT
            if self.__tls_insecure:
                context = ssl._create_unverified_context()
                self.__logger.debug('-> SSL certificate verification is DISABLED')
            else:
                context = None
            conn = http.client.HTTPSConnection(host, port,
                                                timeout=self.__timeout,
                                                context=context)
        else:
            self.__logger.error('Found unmanaged url protocol : "%s" ignoring url', url_parts['proto'])
            return False
        # /PROTOCOL

        # HEADER
        # build the header dict
        headers = {'User-Agent': 'dyndns-update/' + __version__}
        # authentification
        if self.__server_username and self.__server_password:
            # build the auth string
            auth_str = self.__server_username + ':' + self.__server_password
            # encode it as a base64 string to put in http header
            auth = b64encode(auth_str.encode()).decode("ascii")
            # fill the header
            headers['Authorization'] = 'Basic ' + auth
            self.__logger.debug('-> authentication enabled')
        else:
            self.__logger.debug('-> authentication disabled')
        # /HEADER

        # URL
        url = '{base_url}{api_path}?{params}'.format(base_url=url_parts['url'].rstrip('/'),
                                                    api_path=self.__server_api_url,
                                                    params=urllib.parse.urlencode(self.__fields))
        self.__logger.debug('set final url to "%s"', url)
        # /URL

        try:
            conn.request('GET', url, headers=headers)
            res = conn.getresponse()
            data = res.read().decode()
        except socket.gaierror as e:
            self.__logger.debug('=> unable to resolve hostname %s', str(e))
            return False
        except ssl.SSLError as e:
            self.__logger.debug('=> unable to validate the host\'s certifcate.' +
                            ' You can override this by using --insecure')
            return False
        except socket.error as e:
            self.__logger.debug('=> unable to connect to host %s', str(e))
            return False
        except http.client.HTTPException:
            self.__logger.debug('=> error with HTTP query')
            return False
        except Exception as e:
            self.__logger.error('Unhandled python exception please inform the developper %s', str(e))
            return False
        finally:
            conn.close()

        self.__logger.debug('get HTTP status code : %d %s', res.status, res.reason)
        self.__logger.debug('get HTTP data : "%s"', data)

        # authentication missing error
        if res.status == 401:
            self.__logger.debug('=> the server may require an authentification')
            self.__logger.error('The server at url "%s" may require an authentification', url_parts['url'])
            return False
        elif res.status in [200]:
            self.__logger.info('Successfully updated')
            return True
        return False

##
# Run launcher as the main program
if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                        argument_default=argparse.SUPPRESS,
                                        description='DynDNS version v' + __version__ + """ --
Use DYNDNS protocol to update a dynhost with a new ip address""")
    # required arguments
    parser.add_argument('--dyn-address', action='store', dest='dyndns_myip',
                            help='set the IP address to use for update')
    parser.add_argument('--dyn-hostname', action='append', dest='dyndns_hostname',
                            help='set the hostname of the dyn host to update. This is the DNS domain name that point to the ip address')
    parser.add_argument('--dyn-server', action='store', dest='server_url',
                            help='set the dyndns server address that contains the zone to update')

    # optional arguments
    parser.add_argument('-u', '--username', action='store', dest='server_username',
                            help='username to use for http authentication')
    parser.add_argument('-p', '--password', action='store', dest='server_password',
                            help='password to use for http authentication')
    parser.add_argument('--api-url', action='store', dest='server_api_url', default='/nic/update',
                            help='url endpoint to which send http query parameters')

    # dyn dns protocol
    backmx_group = parser.add_mutually_exclusive_group()
    backmx_group.add_argument('--backmx', action='store_true', dest='dyndns_backmx',
                            help='set backupmx option to YES')
    backmx_group.add_argument('--no-backmx', action='store_false', dest='dyndns_backmx',
                            help='set backupmx option to NO')

    wildcard_group = parser.add_mutually_exclusive_group()
    wildcard_group.add_argument('--wildcard', action='store_const', const='ON', dest='dyndns_wildcard',
                            help='set wildcard option to ON')
    wildcard_group.add_argument('--no-wildcard', action='store_const', const='OFF', dest='dyndns_wildcard',
                            help='set wildcard option to OFF')

    parser.add_argument('--url', action='store', dest='dyndns_url',
                            help='url endpoint to which send http query parameters')

    # DynDNS protocol features :

    #     --offline      set dyndns to offline mode (Default: """ + self.__fields['offline'] + """)
    #     --static       set static dns system (Default system : """ + self.__fields['system'] + """)


    parser.add_argument('-t', '--timeout', action='store', dest='timeout', default=5,
                            help='The HTTP timeout in seconds for all requests')
    parser.add_argument('--insecure', action='store', dest='tls_insecure', default=False,
                            help='Disable TLS certificate verification for secure connexions')

    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument('--no-output', action='store_const', dest='verbose', const=-1,
                            help='Disable all output message to stdout. (cron mode)')
    logging_group.add_argument('-v', '--verbose', action='count', dest='verbose',
                            help='Show more running messages')
    parser.add_argument('--errors-to-stderr', action='store_true', dest='errors_to_stderr',
                            help='Copy errors to stderr')
    parser.add_argument('-V', '--version', action='store_true', dest='show_version', default=False,
                            help='Print the version and exit')
    args = parser.parse_args()

    if args.show_version:
        print("DynDNS client version v" + __version__)
        sys.exit(0)

    program = DynDNSUpdate()
    if not program.configure(**vars(args)):
        sys.exit(2)
    sys.exit(program.main())

# Return code :
#     0 Success
#     1 Other errors during running
#     2 Bad argument
#     3 Missing required argument
#     10 Error during HTTP query
#     11 Authentification needed
