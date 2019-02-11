#!/bin/bash

set -e

supervisorconf=/var/www/$1/ebmbot/deploy/supervisord-ebmbot.conf

if [ ! -f $supervisorconf ] ; then
    echo "Unable to find $supervisorconf!"
    exit 1
fi

ln -sf $supervisorconf /etc/supervisor/conf.d/ebmbot.conf
supervisorctl restart ebmbot
