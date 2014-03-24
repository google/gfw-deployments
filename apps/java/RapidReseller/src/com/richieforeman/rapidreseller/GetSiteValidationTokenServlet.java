package com.richieforeman.rapidreseller;

import java.io.IOException;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.google.api.services.siteVerification.SiteVerification;
import com.google.api.services.siteVerification.model.SiteVerificationWebResourceGettokenRequest;
import com.google.api.services.siteVerification.model.SiteVerificationWebResourceGettokenRequest.Site;
import com.google.api.services.siteVerification.model.SiteVerificationWebResourceGettokenResponse;
import com.google.gson.Gson;
import com.richieforeman.rapidreseller.jsonobjects.VerificationTokenJson;

@SuppressWarnings("serial")
public class GetSiteValidationTokenServlet extends RapidResellerServlet {
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws IOException {
		
		String body = this.getRequestBody(req);
		VerificationTokenJson tokenRequest = new Gson().fromJson(body, VerificationTokenJson.class);
		
		SiteVerification service = GoogleAPIUtils.getSiteVerificationService(GoogleAPIUtils.getCredential());
		
		SiteVerificationWebResourceGettokenRequest request = new SiteVerificationWebResourceGettokenRequest()
			.setVerificationMethod(tokenRequest.verificationMethod);
		
		Site site = new Site()
			.setType(tokenRequest.verificationType)
			.setIdentifier(tokenRequest.verificationIdentifier);
		
		request.setSite(site);
		
		SiteVerificationWebResourceGettokenResponse response = service.webResource().getToken(request).execute();
		
		// stick the token inside of the model.
		tokenRequest.verificationToken = response.getToken();
		
		this.sendJson(resp, tokenRequest);
	}
}
