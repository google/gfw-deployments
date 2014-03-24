package com.richieforeman.rapidreseller.jsonobjects;

import com.google.gson.annotations.SerializedName;

public class CustomerJson {
	public String alternateEmail;
	public String domain;
	public String phoneNumber;
	
	@SerializedName("postalAddress.addressLine1")
	public String postalAddress_addressLine1;
	
	@SerializedName("postalAddress.contactName")
	public String postalAddress_contactName;
	
	@SerializedName("postalAddress.countryCode")
	public String postalAddress_countryCode;
	
	@SerializedName("postalAddress.locality")
	public String postalAddress_locality;
	
	@SerializedName("postalAddress.organizationName")
	public String postalAddress_organizationName;
	
	@SerializedName("postalAddress.postalCode")
	public String postalAddress_postalCode;
	
	@SerializedName("postalAddress.region")
	public String postalAddress_region;
	
}
