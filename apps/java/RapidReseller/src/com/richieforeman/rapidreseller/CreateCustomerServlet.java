package com.richieforeman.rapidreseller;

import java.io.IOException;

import javax.servlet.http.*;

import com.google.api.services.reseller.*;
import com.google.api.services.reseller.model.Address;
import com.google.api.services.reseller.model.Customer;
import com.google.gson.Gson;
import com.richieforeman.rapidreseller.jsonobjects.CustomerJson;


@SuppressWarnings("serial")
public class CreateCustomerServlet extends RapidResellerServlet {
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws IOException {
		
		String body = this.getRequestBody(req);
		CustomerJson customerRequest = new Gson().fromJson(body, CustomerJson.class);
		
		Reseller service = GoogleAPIUtils.getResellerService(GoogleAPIUtils.getCredential());
		
		Address address = new Address()
			.setAddressLine1(customerRequest.postalAddress_addressLine1)
			.setContactName(customerRequest.postalAddress_contactName)
			.setOrganizationName(customerRequest.postalAddress_organizationName)
			.setCountryCode(customerRequest.postalAddress_countryCode)
			.setLocality(customerRequest.postalAddress_locality)
			.setRegion(customerRequest.postalAddress_region)
			.setPostalCode(customerRequest.postalAddress_postalCode);
		
		Customer customer = new Customer()
			.setCustomerDomain(customerRequest.domain)
			.setAlternateEmail(customerRequest.alternateEmail)
			.setCustomerId(customerRequest.domain)
			.setPhoneNumber(customerRequest.phoneNumber)
			.setPostalAddress(address);
		
		Customer newCustomer = service.customers().insert(customer).execute(); 
		
		// grab the new domain.
		customerRequest.domain = newCustomer.getCustomerDomain();
		
		this.sendJson(resp, customerRequest);
	}
}
