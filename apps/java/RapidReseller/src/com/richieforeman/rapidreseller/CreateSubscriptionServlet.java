package com.richieforeman.rapidreseller;

import java.io.IOException;

import javax.servlet.http.*;

import com.google.api.services.reseller.*;
import com.google.api.services.reseller.model.RenewalSettings;
import com.google.api.services.reseller.model.Seats;
import com.google.api.services.reseller.model.Subscription;
import com.google.api.services.reseller.model.Subscription.Plan;
import com.google.gson.Gson;
import com.richieforeman.rapidreseller.constants.ResellerPlanName;
import com.richieforeman.rapidreseller.constants.ResellerRenewalType;
import com.richieforeman.rapidreseller.constants.ResellerSKU;
import com.richieforeman.rapidreseller.jsonobjects.SubscriptionJson;


@SuppressWarnings("serial")
public class CreateSubscriptionServlet extends RapidResellerServlet {
	public void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
		
		String body = this.getRequestBody(req);
		SubscriptionJson subscriptionRequest = new Gson().fromJson(body, SubscriptionJson.class);
		
		Reseller service = GoogleAPIUtils.getResellerService(GoogleAPIUtils.getCredential());
		
		Seats seats = new Seats()
			.setMaximumNumberOfSeats(subscriptionRequest.numberOfSeats);
		
		Plan plan = new Plan()
			.setPlanName(ResellerPlanName.FLEXIBLE);
		
		RenewalSettings renewalSettings = new RenewalSettings()
			.setRenewalType(ResellerRenewalType.PAY_AS_YOU_GO);
		
		Subscription subscription = new Subscription()
			.setCustomerId(subscriptionRequest.domain)
			.setSeats(seats)
			.setPlan(plan)
			.setPurchaseOrderId("G00gl39001")
			.setSkuId(ResellerSKU.GoogleApps)
			.setRenewalSettings(renewalSettings);
		
		Subscription newSubscription = service.subscriptions()
				.insert(subscriptionRequest.domain, subscription).execute();
		
		this.sendJson(resp, subscriptionRequest);
		
	}
}
