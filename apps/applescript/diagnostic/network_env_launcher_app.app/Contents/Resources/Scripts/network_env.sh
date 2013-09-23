#!/bin/bash

# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# ###########################################################################
# DISCLAIMER:
#
# (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
# WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
# WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND
#
# (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR
# DATA, OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR
# PUNITIVE DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY,
# EVEN IF GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING
# OUT OF THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS
# CODE OR ITS DERIVATIVES.
#
#
# Collects basic network environment from a user's machine for use in basic
# troubleshooting of networking issues.
#
# This program runs ifconfig, dig, ping, netstat, traceroute.  The ifconfig
# test will log network information for all the interfaces on the machine.
# The ping and traceroute tests are done to Google and non-Google hostnames.
# Output is logged to a file of the format network_env_<TIMESTAMP>.log.
#

#
# Discover the user and change to the desktop
USER=`whoami`

#
# Create the logfile
LOGFILENAME=`date "+network_env_%Y_%m_%d_%H-%M-%S.log"`
touch /Users/$USER/Desktop/$LOGFILENAME
LOGFILE="/Users/$USER/Desktop/$LOGFILENAME"

echo "INFO: Network Environment Capture Starting."
echo "INFO: Network tests may take several minutes."
echo "INFO: Please wait until you received a message that reads \"TEST COMPLETE\"."
echo "INFO: Logging at $LOGFILE"
echo "INFO: Running...."

#
# set the start time
STARTTIME=`date "+%Y_%m_%d_%H-%M-%S"`
echo "INFO: Starting at $STARTTIME"
echo "Starting at $STARTTIME" 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***ifconfig -a***" >> $LOGFILE 2>&1
ifconfig -a >> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***dig +trace +short mail.google.com***" 1>> $LOGFILE 2>&1
dig +trace mail.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***dig +trace +short docs.google.com***" 1>> $LOGFILE 2>&1
dig +trace docs.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***dig +trace +short calendar.google.com***" 1>> $LOGFILE 2>&1
dig +trace calendar.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***dig +trace +short mail.yahoo.com***" 1>> $LOGFILE 2>&1
dig +trace mail.yahoo.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***ping -c 4 mail.google.com***" 1>> $LOGFILE 2>&1
ping -c 4 mail.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***ping -c 4 docs.google.com***" 1>> $LOGFILE 2>&1
ping -c 4 docs.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***ping -c 4 calendar.google.com***" 1>> $LOGFILE 2>&1
ping -c 4 calendar.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***traceroute -a mail.google.com***" 1>> $LOGFILE 2>&1
traceroute -a mail.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***traceroute -a docs.google.com***" 1>> $LOGFILE 2>&1
traceroute -a docs.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***traceroute -a calendar.google.com***" 1>> $LOGFILE 2>&1
traceroute -a calendar.google.com 1>> $LOGFILE 2>&1

echo "" 1>> $LOGFILE 2>&1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" 1>> $LOGFILE 2>&1
echo "***netstat -P ip -s***" 1>> $LOGFILE 2>&1
netstat -P ip -s 1>> $LOGFILE 2>&1

#
# set the end time
ENDTIME=`date "+%Y_%m_%d_%H-%M-%S"`

echo "" 1>> $LOGFILE 2>&1
echo "Finished at $ENDTIME" 1>> $LOGFILENAME 2>&1
echo "INFO: Finished at $ENDTIME"
echo "INFO: TEST COMPLETE"
