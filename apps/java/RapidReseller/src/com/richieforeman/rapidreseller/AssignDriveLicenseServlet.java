package com.richieforeman.rapidreseller;

import java.io.IOException;

import javax.servlet.http.*;

import com.google.gson.Gson;
import com.richieforeman.rapidreseller.constants.ResellerProduct;
import com.richieforeman.rapidreseller.constants.ResellerSKU;
import com.google.api.services.licensing.Licensing;
import com.google.api.services.licensing.model.LicenseAssignment;
import com.google.api.services.licensing.model.LicenseAssignmentInsert;
import com.richieforeman.rapidreseller.jsonobjects.AssignJson;


@SuppressWarnings("serial")
public class AssignDriveLicenseServlet extends RapidResellerServlet {
	public void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
		
		String body = this.getRequestBody(req);
		AssignJson assignRequest = new Gson().fromJson(body, AssignJson.class);
		
		Licensing service = GoogleAPIUtils.getAdminLicensingService(GoogleAPIUtils.getCredential());
		
		LicenseAssignmentInsert license = new LicenseAssignmentInsert()
			.setUserId("admin@" + assignRequest.domain);
		
		service.licenseAssignments().insert(
				ResellerProduct.GOOGLE_DRIVE_STORAGE, 
				ResellerSKU.GoogleDriveStorage20GB, 
				license).execute();
		
		this.sendJson(resp, assignRequest);
	}
}

