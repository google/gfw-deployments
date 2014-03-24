package com.richieforeman.rapidreseller;

import java.io.IOException;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.google.api.services.siteVerification.SiteVerification;
import com.google.api.services.siteVerification.model.SiteVerificationWebResourceResource.Site;
import com.google.api.services.siteVerification.model.SiteVerificationWebResourceResource;
import com.google.gson.Gson;
import com.richieforeman.rapidreseller.jsonobjects.VerificationTokenJson;

@SuppressWarnings("serial")
public class TestSiteValidationTokenServlet extends RapidResellerServlet {
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws IOException {
		
		String body = this.getRequestBody(req);
		VerificationTokenJson tokenRequest = new Gson().fromJson(body, VerificationTokenJson.class);
		
		SiteVerification service = GoogleAPIUtils.getSiteVerificationService(GoogleAPIUtils.getCredential());

		SiteVerificationWebResourceResource resource = new SiteVerificationWebResourceResource();
		
		Site site = new Site()
			.setIdentifier(tokenRequest.verificationIdentifier)
			.setType(tokenRequest.verificationType);
		resource.setSite(site);

		service.webResource().insert(tokenRequest.verificationMethod, resource).execute();
		
		this.sendJson(resp, tokenRequest);
	}
}
