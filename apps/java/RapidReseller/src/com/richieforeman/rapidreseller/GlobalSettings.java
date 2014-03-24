package com.richieforeman.rapidreseller;

import java.util.Arrays;
import java.util.List;

import com.google.api.services.reseller.ResellerScopes;
import com.google.api.services.siteVerification.SiteVerificationScopes;
import com.google.api.services.admin.directory.DirectoryScopes;

public class GlobalSettings {
	public static final String SERVICE_ACCOUNT_EMAIL = 
			"801883730557-744ngc0s9eh5md75gehkb98acppjjr61@developer.gserviceaccount.com";
	
	public static final String PRIVATE_KEY_FILE = "privatekey.p12";
	
	public static final String RESELLER_ADMIN = "richieforeman@reseller.gappslabs.co";
	
	public static final List<String> SCOPES = Arrays.asList(
			ResellerScopes.APPS_ORDER,
			SiteVerificationScopes.SITEVERIFICATION,
			DirectoryScopes.ADMIN_DIRECTORY_USER,
			// The Licensing API does not include a constant... :/
			"https://www.googleapis.com/auth/apps.licensing"
	);
}
