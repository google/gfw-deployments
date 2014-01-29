echo "Installing Google Python Client Library Dependencies..."
curl -o /tmp/google-api-python-client-gae-1.2.zip http://google-api-python-client.googlecode.com/files/google-api-python-client-gae-1.2.zip
unzip -f /tmp/google-api-python-client-gae-1.2.zip

sudo npm install -g bower
sudo npm install -g grunt-cli

npm install
bower install
grunt build:all