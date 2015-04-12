#!/bin/bash

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

#title      :dyn_update.sh
#description:Use DYN protocol for updating a dynhost with a new ip address
#author      :P.GINDRAUD
#author_contact  :pgindraud@gmail.com
#date      :2014-04-10
#usage      :./dyn_update.sh
#usage_info  :
#options    :NONE
#notes      :
#
#versions_notes  :
#  version 2.0 : 2014-06-28
#        +refund all script syntax the follow the current norm
#        +adding some documentations strings
VERSION='2.0'
#==============================================================================


#========== INTERNAL OPTIONS ==========#
readonly WGET_PATH=$(which wget 2>/dev/null)

# static url data for mean that you want to edit a dyn host
DYN_NIC='/nic/update'


#========== INTERNAL VARIABLES ==========#
USER_AGENT="dyn_update/$VERSION"
HTTP_GLOBAL_OPTS="--user-agent=$USER_AGENT"

IS_DEBUG=0
IS_VERBOSE=0

# remote server to which send dyn update string
DYNDNS_SERVER='members.dyndns.org'
# username use to make dyn update
DYNDNS_USERNAME=''
# dyn password associate to above username
DYNDNS_PASSWORD=''
# the dns hostname to update
DYNDNS_HOSTNAME=''


### DYN DNS SYNTAX DOCUMENTATION
# for detail see https://help.dyn.com/remote-access-api/perform-update/
# Use to identify update type
#   0 (="dyndns")
#  1 (="statdns")
IF_SYSTEM_STATIC=0

# A comma separated list of host to update (max 20)
HOSTNAME=

# The IP address to set. If not set or incorrect the server will choose himself an IP
MYIP=

#   1 (="ON")
#   0 (="NOCHG")
#   -1 (="OFF")
IF_WILDCARD=0

# Specify an eMail eXchanger
#
MX=

#   1 ("YES")
#   O ("NOCHG") no make change
#   -1 (="NO")
IF_BACKMX=0

# Set the hostname to offline mode
#   1 (="YES") turn on offline redirect for host
#   0 (="NOCHG") no make change
IF_OFFLINE=0

# No already use
URL=



#========== INTERNAL FUNCTIONS ==========#
# Print help msg
function _usage() {
  echo -e "Usage : $0 [OPTION] USERNAME PASSWORD DYN_HOSTNAME

Use DYN protocol for updating a dynhost with a new ip address

Arguments :
  USERNAME  dyn host to make authentication to server
  PASSWORD  password associate to the USERNAME
  DYN_HOSTNAME  dynhost name with the ip to update

Options :
  -a, --address=IP_ADDRESS  set manually the IP address to use for update the A
                      field instead of the build-in lookup (Recommanded)
  -d, --destination=IP/HOST  set the dyndns server address that contains
                      the zone to update (Default: '${DYNDNS_SERVER}')
  -h, --help     print this help message
  -v, --verbose  show more running messages
  -vv, --debug   show debug messages

Dyndns protocol :
  -b, --backupmx      set backup mx option YES (Default: NOCHG)
  -!b, --no-backupmx  unset backup mx option NO (Default: NOCHG)
  -o, --offline       set dyndns to offline mode
  -s, --static        set static dns option (Default: dynamic)
  -w, --wildcard      set wildcard ON (Default: NOCHG)
  -!w, --no-wildcard  unset wildcard OFF (Default: NOCHG)"
}

# Print a msg to stdout if verbose option is set
# @param[string] : the msg to write in stdout
function _echo() {
  if [[ $IS_VERBOSE -eq 1 ]]; then
    echo -e "$@"
  fi
}

# Print a msg to stderr if verbose option is set
# @param[string] : the msg to write in stderr
function _error() {
  if [[ $IS_VERBOSE -eq 1 ]]; then
    echo -e "Error : $@" 1>&2
  fi
}

# Print a msg to stdout if debug verbose is set
# @param[string] : the msg to write in stdout
function _debug() {
  if [[ $IS_DEBUG -eq 1 ]]; then
    echo -e "debug: $@"
  fi
}

# Print a msg to stderr and quit
# param[in](string) : the msg to write in stderr
function _errorq() {
  echo "$0: $@" 1>&2
  exit 2
}

# Print a msg to stderr and suggest to read help to user quit
# param[in](string) : the msg to write in 2
function _errorqh() {
  _error "$@"
  echo "Try '$0 --help' for more information." 1>&2
  exit 2
}

# Build the url option with input parameters
function _makeQuery() {
  local http_data=

  #SYSTEM OPTION
  if [[ $IF_SYSTEM_STATIC -eq 1 ]]; then
    http_data="${http_data}system=statdns"
  else
    http_data="${http_data}system=dyndns"
  fi

  #ADD HOSTNAME OF ENTRY TO UPDATE
  http_data="${http_data}&hostname=${DYNDNS_HOSTNAME}"

  # IP DEFINITION
  if [[ $IF_OFFLINE -eq 1 ]]; then
    http_data="${http_data}&offline=YES"
  else
    http_data="${http_data}&myip=${MYIP}"
  fi

  # OPTION WILDCARD
  if [[ $IF_WILDCARD -eq 1 ]]; then
    http_data="${http_data}&wildcard=ON"
  elif [[ $IF_WILDCARD -eq -1 ]]; then
    http_data="${http_data}&wildcard=OFF"
  else
    http_data="${http_data}&wildcard=NOCHG"
  fi

  # OPTION BACKMX
  if [[ $IF_BACKMX -eq 1 ]]; then
    http_data="${http_data}&backmx=YES"
  elif [[ $IF_WILDCARD -eq -1 ]]; then
    http_data="${http_data}&backmx=NO"
  else
    http_data="${http_data}&backmx=NOCHG"
  fi

  _query "$http_data"
}



# Send GET query to server by using the option string give by parameter
# param[in](string) : http data to include in the query
function _query() {
  local opts="--quiet --http-user=$DYNDNS_USERNAME --http-password=${DYNDNS_PASSWORD}"
  local query="http://${DYNDNS_SERVER}${DYN_NIC}?$1"
  _debug "query = '${query}'"

  #  opts="$opts --post-data $1"

  if [[ $IS_VERBOSE -eq 1 ]]; then
    ${WGET_PATH} $HTTP_GLOBAL_OPTS $opts --output-document=- "$query"
    echo
  else
    ${WGET_PATH} $HTTP_GLOBAL_OPTS $opts --output-document=- "$query" > /dev/null 2>&1
  fi
}



#========== MAIN FUNCTION ==========#

# Main
# param  :same of the script
# return  :
function main() {
  ##PARSING ARGUMENTS
  #number of needed arguments
  local MAIN_REQUIRED_ARGUMENTS=3
  for i in `seq $(($#+1))`; do
    #catch main arguments
    case $1 in
      -a) shift; MYIP="$1";;
      --address=*) MYIP=`echo $1 | cut -d '=' -f 2-`;;
      -b|--backupmx) IF_BACKMX=1;;
      -!b|--no-backupmx) IF_BACKMX=-1;;
      -d) shift; DYNDNS_SERVER="$1";;
      --destination=*) DYNDNS_SERVER=`echo $1 | cut -d '=' -f 2-`;;
      -h|--help) _usage; exit 0;;
      -o|--offline) IF_OFFLINE=1;;
      -s|--static) IF_SYSTEM_STATIC=1;;
      -v|--verbose) IS_VERBOSE=1;;
      -vv|--debug) IS_DEBUG=1;;
      -w|--wildcard) IF_WILDCARD=1;;
      -!w|--no-wildcard) IF_WILDCARD=-1;;
      -*) _errorqh "invalid option -- '$1'";;
      *)
        if [[ $# -ge $MAIN_REQUIRED_ARGUMENTS ]]; then
          # GOT NEEDED ARGUMENTS
          DYNDNS_USERNAME=$1
          DYNDNS_PASSWORD=$2
          DYNDNS_HOSTNAME=$3
          break;#stop reading arguments
        else
          _errorqh 'missing operand'
        fi
      ;;
    esac
  shift
  done

  if [[ -z $WGET_PATH ]]; then
    _errorq "Wget not found, please install it or check your configuration"
  fi

  # check ip address
  if [[ -z $MYIP ]]; then
    MYIP="0.0.0.0"
    _error 'no ip address given, using the default 0.0.0.0'
  fi

  if [[ $IF_OFFLINE -eq 1 ]]; then _debug 'set OPTION offline'; fi
  if [[ $IF_SYSTEM_STATIC -eq 1 ]]; then _debug 'set OPTION static dns'; fi
  if [[ $IF_WILDCARD -eq 1 ]]; then _debug 'set OPTION wildcard to ON'; fi
  if [[ $IF_WILDCARD -eq -1 ]]; then _debug 'set OPTION wildcard to OFF'; fi
  _debug "set username to $DYNDNS_USERNAME"
  if [[ $IS_DEBUG -eq 1 ]]; then
    local password_string=
    for i in `seq ${#DYNDNS_PASSWORD}`; do
      password_string=`echo -n "$password_string*"`
    done
  fi
  _debug "set password to $password_string"
  _debug "set hostname to ${DYNDNS_HOSTNAME}"
  _debug "set dyn server to ${DYNDNS_SERVER}"
  _debug "using ip address: ${MYIP}"
  
  _makeQuery
}

main "$@"