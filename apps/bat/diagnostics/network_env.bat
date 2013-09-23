REM Copyright 2010 Google Inc. All Rights Reserved.
REM
REM Licensed under the Apache License, Version 2.0 (the "License");
REM you may not use this file except in compliance with the License.
REM You may obtain a copy of the License at
REM
REM http://www.apache.org/licenses/LICENSE-2.0
REM
REM ###########################################################################
REM DISCLAIMER:
REM
REM (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
REM WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
REM WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
REM PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND
REM
REM (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR
REM DATA, OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR
REM PUNITIVE DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY,
REM EVEN IF GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING
REM OUT OF THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS
REM CODE OR ITS DERIVATIVES.
REM
REM
REM Collects basic network environment from a user's machine for use in basic
REM troubleshooting of networking issues.
REM
REM This program runs ping, tracert, and ipconfig.  The ping and tracert tests
REM are done to Google and non-Google hostnames.  Output is logged to a file
REM of the format network_env<USERNAME>_<TIMESTAMP>.log.
REM

@ECHO OFF
cls

REM get timestamp
set cur_yyyy=%date:~10,4%
set cur_mm=%date:~4,2%
set cur_dd=%date:~7,2%
set cur_hh=%time:~0,2%
if %cur_hh% lss 10 (set cur_hh=0%time:~1,1%)
set cur_nn=%time:~3,2%
set cur_ss=%time:~6,2%
set cur_ms=%time:~9,2%
set timestamp=%cur_yyyy%%cur_mm%%cur_dd%-%cur_hh%%cur_nn%%cur_ss%%cur_ms%

set log_file=network_env_%username%_%timestamp%.log

ECHO INFO: Network Env Capture Starting at: %DATE% %TIME%
ECHO INFO: Network tests may take several minutes.
ECHO INFO: Please wait until you received a message that reads "TEST COMPLETE"
ECHO INFO: Running....

ECHO Starting at %DATE% %TIME% > %log_file%

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***ipconfig /all*** 1>> %log_file% 2>&1
ipconfig /all 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***nslookup mail.google.com*** 1>> %log_file% 2>&1
nslookup mail.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***nslookup docs.google.com*** 1>> %log_file% 2>&1
nslookup docs.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***nslookup calendar.google.com*** 1>> %log_file% 2>&1
nslookup calendar.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***nslookup mail.yahoo.com*** 1>> %log_file% 2>&1
nslookup mail.yahoo.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***ping mail.google.com*** 1>> %log_file% 2>&1
ping -s 4 mail.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***ping docs.google.com*** 1>> %log_file% 2>&1
ping -s 4 docs.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***ping calendar.google.com*** 1>> %log_file% 2>&1
ping -s 4 calendar.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***tracert mail.google.com*** 1>> %log_file% 2>&1
tracert -d mail.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***pathping -n mail.google.com*** 1>> %log_file% 2>&1
pathping -n mail.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***tracert docs.google.com*** 1>> %log_file% 2>&1
tracert -d docs.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***pathping -n docs.google.com*** 1>> %log_file% 2>&1
pathping -n docs.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***tracert calendar.google.com*** 1>> %log_file% 2>&1
tracert -d calendar.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***pathping -n calendar.google.com*** 1>> %log_file% 2>&1
pathping -n calendar.google.com 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***netstat -r*** 1>> %log_file% 2>&1
netstat -r 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***netstat -s -P tcp*** 1>> %log_file% 2>&1
netstat -s -P tcp 1>> %log_file% 2>&1

REM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ECHO ***netstat -s -P ip*** 1>> %log_file% 2>&1
netstat -s -P ip 1>> %log_file% 2>&1

ECHO Finished at %DATE% %TIME% 1>> %log_file% 2>&1
ECHO Finished at %DATE% %TIME%

ECHO INFO: TEST COMPLETE
PAUSE
