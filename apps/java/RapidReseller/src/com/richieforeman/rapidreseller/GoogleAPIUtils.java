package com.richieforeman.rapidreseller;

import com.google.api.client.http.HttpTransport;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.services.admin.directory.Directory;
import com.google.api.services.reseller.Reseller;
import com.google.api.services.siteVerification.SiteVerification;
import com.google.api.services.licensing.Licensing;
import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.http.javanet.NetHttpTransport;


import java.io.File;
import java.io.IOException;
import java.security.GeneralSecurityException;

public class GoogleAPIUtils {
	private static final HttpTransport HTTP_TRANSPORT = new NetHttpTransport();
	private static final JsonFactory JSON_FACTORY = new JacksonFactory();
	
	private static final String ApplicationName = "RapidReseller";
	
	public static GoogleCredential getCredential() throws IOException {
		GoogleCredential credentials = null;
		
		try {
			credentials = new GoogleCredential.Builder()
				.setTransport(HTTP_TRANSPORT)
				.setJsonFactory(JSON_FACTORY)
				.setServiceAccountId(GlobalSettings.SERVICE_ACCOUNT_EMAIL)
				.setServiceAccountScopes(GlobalSettings.SCOPES)
				.setServiceAccountUser(GlobalSettings.RESELLER_ADMIN)
				.setServiceAccountPrivateKeyFromP12File(new File(GlobalSettings.PRIVATE_KEY_FILE))
				.build();
		} catch (GeneralSecurityException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		return credentials;
	}
	public static Reseller getResellerService(GoogleCredential credentials) {
		Reseller service = new Reseller.Builder(HTTP_TRANSPORT, JSON_FACTORY, credentials)
			.setApplicationName(ApplicationName).build();
		return service;
	}
	
	public static SiteVerification getSiteVerificationService(GoogleCredential credentials) {
		SiteVerification service = new SiteVerification.Builder(HTTP_TRANSPORT, JSON_FACTORY, credentials)
			.setApplicationName(ApplicationName).build();
		return service;
	}
	
	public static Directory getAdminDirectoryService(GoogleCredential credentials) {
		Directory service = new Directory.Builder(HTTP_TRANSPORT, JSON_FACTORY, credentials)
			.setApplicationName(ApplicationName).build();
		return service;
	}
	
	public static Licensing getAdminLicensingService(GoogleCredential credentials) {
		Licensing service = new Licensing.Builder(HTTP_TRANSPORT, JSON_FACTORY, credentials)
			.setApplicationName(ApplicationName).build();
		return service;
	}
}
