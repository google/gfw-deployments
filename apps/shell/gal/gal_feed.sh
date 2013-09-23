#!/bin/bash
#Usage <SCRIPT_NAME> <DOMAIN> <EMAIL_ADDRESS> <PASSWORD>
#Output file will be written to <domain>_<date-time>.xml

domain=$1
email=$2
passwd=$3

d=`date +%m%d%Y-%H%M%S`
url="https://www.google.com/m8/feeds/gal/$domain/full"
oldurl=""

auth=`curl https://www.google.com/accounts/ClientLogin -d Email=$email -d Passwd=$passwd -d accountType=HOSTED -d service=cp | grep "Auth=" | awk -F"=" '{print $2}'`

while [ -n $url ]
do
     curl --silent --header "Authorization: GoogleLogin auth=$auth" --header "GData-Version: 1.0" "$url" 2> /dev/null > ./gal_dump.xml; xmllint --format ./gal_dump.xml> ./temp_gal.xml
     url=`cat temp_gal.xml | grep next| awk '{print $4}' | awk -F"\"" '{print $2}'`
     cat temp_gal.xml >> $domain"_$d.xml"
     if [ "$oldurl" == "$url" ]
     then
          break
     fi
     oldurl=$url
     echo "New: $url"
done
