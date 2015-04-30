function FindProxyForURL(url, host) {
  
	// Plain hostnames. ( e.g. http://server )
	if (isPlainHostName(host)) {
		return "DIRECT";
	}
	
	// Private address classes.
	if (isInNet(dnsResolve(host), "10.0.0.0", "255.0.0.0") ||
	    isInNet(dnsResolve(host), "172.16.0.0",  "255.240.0.0") ||
	    isInNet(dnsResolve(host), "192.168.0.0", "255.255.0.0") ||
	    isInNet(dnsResolve(host), "127.0.0.0", "255.255.255.0")) {
		return "DIRECT";
	}
 
	// Google Netblocks (_netblocks.google.com)
	// 216.239.32.0/19 
	// 64.233.160.0/19 
	// 66.249.80.0/20 
	// 72.14.192.0/18 
	// 209.85.128.0/17 
	// 66.102.0.0/20 
	// 74.125.0.0/16 
	// 64.18.0.0/20 
	// 207.126.144.0/20 
	// 173.194.0.0/16
	if (isInNet(dnsResolve(host), '216.239.32.0', '255.255.224.0') ||
	    isInNet(dnsResolve(host), '64.233.160.0', '255.255.224.0') ||
	    isInNet(dnsResolve(host), '66.249.80.0', '255.255.240.0') ||
	    isInNet(dnsResolve(host), '72.14.192.0', '255.255.192.0') ||
	    isInNet(dnsResolve(host), '209.85.128.0', '255.255.128.0') ||
	    isInNet(dnsResolve(host), '66.102.0.0', '255.255.240.0') ||
	    isInNet(dnsResolve(host), '74.125.0.0', '255.255.0.0') ||
	    isInNet(dnsResolve(host), '64.18.0.0', '255.255.240.0') ||
	    isInNet(dnsResolve(host), '207.126.144.0', '255.255.240.0') ||
	    isInNet(dnsResolve(host), '173.194.0.0', '255.255.0.0')) {
		return "DIRECT";
	}
 
	// Catch any wildcard Google domains that have fallen through.
	if (shExpMatch(url, "https://*.google.com/*") || 
	    shExpMatch(url, "https://*doubleclick.net/*") ||
	    shExpMatch(url, "https://*gmail.com/*") ||
	    shExpMatch(url, "https://*google-analytics.com/*") ||
	    shExpMatch(url, "https://*googleadservices.com/*") ||
	    shExpMatch(url, "https://*googleapis.com/*") ||
	    shExpMatch(url, "https://*googleusercontent.com/*") ||
	    shExpMatch(url, "https://*gstatic.com/*") ||
	    shExpMatch(url, "https://*ggpht.com/*") ||
	    shExpMatch(url, "https://*ytimg.com/*")) {
		return "DIRECT";
	}
 
 
	// Default rule falls back to the proxy servers.
	return "PROXY myproxyserver.corp.mycompany.com:3128; PROXY myproxyserver2.corp.mycompany.com:3128";
}
