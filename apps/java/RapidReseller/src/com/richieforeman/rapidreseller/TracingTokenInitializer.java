package com.richieforeman.rapidreseller;

import com.google.api.client.googleapis.services.AbstractGoogleClientRequest;
import com.google.api.client.googleapis.services.GoogleClientRequestInitializer;

public class TracingTokenInitializer implements GoogleClientRequestInitializer {

	@Override
	public void initialize(AbstractGoogleClientRequest<?> req) {
		System.out.println("Init tracing token.....");
		req.put("trace", "token:<<TOKEN GOES HERE>>");
	}
}