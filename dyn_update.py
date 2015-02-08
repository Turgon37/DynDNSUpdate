#!/usr/bin/python3
# -*- coding: utf8 -*-

# This file is a part of DynUpdate
#
# Copyright (c) 2014-2015 Pierre GINDRAUD
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

"""DynUpdate program

A simple dyndns client
https://github.com/Turgon37/DynUpdate
"""

# System imports
from base64 import b64encode
import getopt
from http.client import HTTPConnection
import logging
import re
import sys

# Global project declarations
version = '1.0'

class DynUpdate:
  """An instance of a dyn client
  
  This class represent a instance of a dyn dns client until it make
  his http query to update a remote dns server entry
  """

  def __init__(self):
    """Constructor : Build an launcher for dynupdate
    """
    self._argv = None
    
    # Network required
    self._username = ''
    self._password = ''
    self._server = ''
    self._port = 80
    self._url = '/nic/update'
    self._logger = logging.getLogger('dynupdate'+version)
    self._logger.setLevel('INFO')
    hdlr = logging.StreamHandler(sys.stdout)
    self._logger.addHandler(hdlr)
    
    # DYNDNS protocol
    # for detail see https://help.dyn.com/remote-access-api/perform-update/
    self._fields = dict()
    
    # Identify update type
    # "dyndns", "statdns"
    self._fields['system'] = 'dyndns'
    
    # A comma separated list of host to update (max 20)
    self._fields['hostname'] = ''
    
    # The IP address to set. 
    # If not set or incorrect the server will choose himself an IP
    self._fields['myip'] = ''
    
    # Parameter enables or disables wildcards for this host.
    # Values : "ON","NOCHG","OFF"
    self._fields['wildcard'] = 'NOCHG'
    
    # Specify an eMail eXchanger
    self._fields['mx'] = ''
    
    # Requests the MX in the previous parameter to be set up as a backup MX
    # by listing the host itself as an MX with a lower preference value.
    # Values : "ON","NOCHG","OFF"
    self._fields['backmx'] = 'NOCHG'

    # Set the hostname to offline mode
    # "YES" turn on offline redirect for host
    # "NOCHG" no make change
    self._fields['offline'] = 'NOCHG'
    
    # No already use
    self._fields['url'] = ''

  def showVersion(self):
    """Shows the program version
    """
    print("dyn update version v"+version)

  def showUsage(self):
    """Prints command line options
    """
    print('Usage: '+self._argv[0]+' REQUIRED [OPTIONS...]')
    print('')
    print('Dyn update client v'+version)
    print('Use DYNDNS protocol for updating a dynhost with a new ip address')
    print('')
    print('Required :')
    print('    -a, --address=IP_ADDRESS   set the IP address to use for update')
    print('    -h, --hostname=HOSTNAME    set the IP address to use for update')
    print('    -s, --server=HOST|ADDR     set the dyndns server address that contains the zone to update')
    print('Options :')
    print('    -u, --username=NAME    username to use for http authentication')
    print('    -p, --password=PASS    password to use for http authentication')
    print('    --port=PORT            port to use to send get query to server (Default '+str(self._port)+')')
    print('    --api=URL              url to send http parameters  (Default '+str(self._url)+')')
    print('    --help               display this help message')
    print('    --no-output          disable all output')
    print('    -v, --verbose        show more running messages')
    print('    -V, --version        print the version')
    print('DynDNS protocol facilities :')
    print('    --backmx       set backupmx option YES (Default: '+str(self._fields['backmx'])+')')
    print('    --no-backmx    set backupmx option NO (Default: '+str(self._fields['backmx'])+')')
    print('    --offline      set dyndns to offline mode (Default: '+str(self._fields['offline'])+')')
    print('    --static       set static dns system (Default: '+str(self._fields['system'])+')')
    print('    --wildcard     set wildcard ON (Default: '+str(self._fields['wildcard'])+')')
    print('    --no-wildcard  set wildcard OFF (Default: '+str(self._fields['wildcard'])+')')
    print('    --url=  set dyndns url feature')

  def _parseCmdLineOptions(self, options_list):
    """Parse input main options, and apply rules
    
    @param(dict) options_list : array of option key => value
    """
    for opt in options_list:
      if opt[0] in ['-a', '--address']:
        self._fields['myip'] = opt[1]
      if opt[0] in ['-h', '--hostname']:
        self._fields['hostname'] = opt[1]
      if opt[0] in ['-u', '--username']:
        self._username = opt[1]
      if opt[0] in ['-p', '--password']:
        self._password = opt[1]
      if opt[0] in ['-s', '--server']:
        self._server = opt[1]
      if opt[0] == '--port':
        self._port = int(opt[1])
      if opt[0] == '--api':
        self._url = opt[1]
      
      if opt[0] in ['-v', '--verbose']:
        self._logger.setLevel('DEBUG')
      if opt[0] == '--no-output':
        # disable logging
        logging.disable(logging.CRITICAL+1)
        
      if opt[0] == '--backmx':
        self._fields['backmx'] = 'YES'
      if opt[0] == '--no-backmx':
        self._fields['backmx'] = 'NO'
      if opt[0] == '--offline':
        self._fields['offline'] = 'YES'
      if opt[0] == '--static':
        self._fields['system'] = 'statdns'
      if opt[0] == '--wildcard':
        self._fields['wildcard'] = 'YES'
      if opt[0] == '--no-wildcard':
        self._fields['wildcard'] = 'NO'
      if opt[0] == '--url':
        self._fields['url'] = opt[1]
        
      if opt[0] == '--help':
        self.showUsage()
        sys.exit(0)
      if opt[0] in ['-V', '--version']:
        self.showVersion()
        sys.exit(0)

  def start(self, argv):
    """Entry point of the launcher
    
    @param(dict) argv : array of shell options given by main function
    """
    # save the arg vector
    self._argv = argv

    # read the only allowed command line options
    try:
      short_opts = 'a:h:u:p:s:vV'
      long_opts = ['address=',
                  'hostname=',
                  'username=', 
                  'password=',
                  'server=',
                  'port=',
                  'api=',
                  'no-output', 'verbose',
                  'backmx', 'no-backmx', 'offline', 'static', 
                  'wildcard', 'no-wildcard', 'url=',
                  'help', 'version']
      options_list, args = getopt.getopt(argv[1:], short_opts, long_opts)
      self._parseCmdLineOptions(options_list)
    except getopt.GetoptError as e:
      self._logger.error(e)
      self._logger.error('')
      self.showUsage()
      return False
    except Exception as e:
      self._logger.error('Problem during parameters interpretation :')
      self._logger.error('   '+str(e))
      return False
    
    try:
      for val in [self._server,
                  self._fields['myip'],
                  self._fields['hostname'],
                  ]:
        if not val:
          raise Exception('missing a required argument use --help')
      self._logger.debug('debug: run with field '+str(self._fields))
      return self.query()
    except Exception as e:
      self._logger.error(e)
      return False

  def query(self):
    """Forge and send the get query
    
    @return(boolean) : True if query success
                        False otherwise
    """
    # bulding url
    url = '/'+self._url.strip('/')+'?hostname='+self._fields['hostname']
    for param in self._fields:
      if self._fields[param] and param not in ['hostname']:
        url += '&'+param+'='+self._fields[param]
    self._logger.debug('debug: url set to : "'+url+'"')
    # /bulding url
    
    h = HTTPConnection(self._server, self._port, timeout = 1)
    self._logger.debug('debug: query to : '+self._server+':'+str(self._port))
    try:
      headers = { 'User-Agent' : 'dyn_update/'+version }
      
      if self._username and self._password:
        self._logger.debug('debug: authentication enable')
        auth_str = self._username+':'+self._password
        auth = b64encode(auth_str.encode()).decode("ascii")
        headers['Authorization'] = 'Basic '+auth
      else:
        self._logger.debug('debug: authentication disable')
        
      h.request('GET', url, headers=headers)
      res = h.getresponse()
      
      # Use during developpement
      #headers = res.getheaders()
      #for head in headers:
      #  print(head)
      self._logger.debug('debug: get status '+str(res.status)+' '+str(res.reason))
      self._logger.debug('debug: '+str(res.read()))
      if res.status == 401:
        self._logger.error('The server require a authentification')
        return False
      elif res.status == 200:
        self._logger.info('Success')
        return True
      
    except Exception as e:
      self._logger.error('unable to reach the host '+str(e))
      return False
    
##
# Run launcher as the main program
if __name__ == '__main__':
  instance = DynUpdate();
  if instance.start(sys.argv):
    sys.exit(0)
  else:
    sys.exit(-1)
