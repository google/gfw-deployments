echo "Installing Google Python Client Library Dependencies..."
curl -o /tmp/google-api-python-client-gae-1.2.zip https://google-api-python-client.googlecode.com/files/google-api-python-client-gae-1.2.zip
unzip -f /tmp/google-api-python-client-gae-1.2.zip

npm install -g bower
npm install -g grunt-cli

npm install
bower install
grunt