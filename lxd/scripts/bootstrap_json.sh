#!/bin/bash
#
# My Boostrap script for my LXD Containers.
#
# Lost of code stolen from: https://github.com/saltstack/salt-bootstrap/blob/develop/bootstrap-salt.sh


set -o nounset # Treat unset variables as an error

#---  FUNCTION  -------------------------------------------------------------------------------------------------------
#          NAME:  echoerr
#   DESCRIPTION:  Echo errors to stderr.
#----------------------------------------------------------------------------------------------------------------------
echoerror() {
    printf "${RC} * ERROR${EC}: %s\n" "$@" 1>&2;
}

#---  FUNCTION  -------------------------------------------------------------------------------------------------------
#          NAME:  echoinfo
#   DESCRIPTION:  Echo information to stdout.
#----------------------------------------------------------------------------------------------------------------------
echoinfo() {
    printf "${GC} *  INFO${EC}: %s\n" "$@";
}

#---  FUNCTION  -------------------------------------------------------------------------------------------------------
#          NAME:  echowarn
#   DESCRIPTION:  Echo warning informations to stdout.
#----------------------------------------------------------------------------------------------------------------------
echowarn() {
    printf "${YC} *  WARN${EC}: %s\n" "$@";
}

# Bootstrap script truth values
BS_TRUE=1
BS_FALSE=0

#---  FUNCTION  -------------------------------------------------------------------------------------------------------
#          NAME:  __detect_color_support
#   DESCRIPTION:  Try to detect color support.
#----------------------------------------------------------------------------------------------------------------------
_COLORS=${BS_COLORS:-$(tput colors 2>/dev/null || echo 0)}
__detect_color_support() {
    if [ $? -eq 0 ] && [ "$_COLORS" -gt 2 ]; then
        RC="\033[1;31m"
        GC="\033[1;32m"
        BC="\033[1;34m"
        YC="\033[1;33m"
        EC="\033[0m"
    else
        RC=""
        GC=""
        BC=""
        YC=""
        EC=""
    fi
}
__detect_color_support

# whoami alternative for SunOS
if [ -f /usr/xpg4/bin/id ]; then
    whoami='/usr/xpg4/bin/id -un'
else
    whoami='whoami'
fi

# Root permissions are required to run this script
if [ "$(${whoami})" != "root" ]; then
    echoerror "${0} requires root privileges to install. Please re-run this script as root."
    exit 1
fi


if [[ ${#@} -ne 4 ]]; then
    echoerror "Usage: ${0} <hostname> <domainname> <minion-json-config> <version>"
    exit 1
fi

echoinfo "Setting the domainname to ${2}"
/bin/echo "$1" > /etc/hostname
/bin/sed -i 's/127\.0\.1\.1.*//g' /etc/hosts
/bin/echo -e "127.0.1.1\t${1}.${2} ${1}" >> /etc/hosts

echoinfo "Update current software"
/usr/bin/apt-get update
/usr/bin/apt-get -qy -o 'DPkg::Options::=--force-confold' -o 'DPkg::Options::=--force-confdef' dist-upgrade

if [ -d /home/ubuntu ]; then
    echoinfo "Deleting user \"ubuntu\""
    /usr/sbin/userdel -r "ubuntu"
fi

echoinfo "Install salt-minion"
/usr/bin/apt-get -qy -o 'DPkg::Options::=--force-confold' -o 'DPkg::Options::=--force-confdef' install wget
cd /root
/usr/bin/wget -O bootstrap_salt.sh https://bootstrap.saltstack.com
/bin/sh /root/bootstrap_salt.sh -j "${3}" ${4}
rm -f /root/boostrap_salt.sh
