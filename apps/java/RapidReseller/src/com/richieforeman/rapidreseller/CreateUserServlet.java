package com.richieforeman.rapidreseller;

import java.io.IOException;

import javax.servlet.http.*;

import com.google.gson.Gson;
import com.google.api.services.admin.directory.Directory;
import com.google.api.services.admin.directory.model.User;
import com.google.api.services.admin.directory.model.UserName;
import com.google.api.services.admin.directory.model.UserMakeAdmin;
import com.richieforeman.rapidreseller.jsonobjects.UserJson;


@SuppressWarnings("serial")
public class CreateUserServlet extends RapidResellerServlet {
	public void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
		
		String body = this.getRequestBody(req);
		UserJson userRequest = new Gson().fromJson(body, UserJson.class);
		
		String username = "admin@" + userRequest.domain;
		String password = "P@ssw0rd!!";
		
		Directory service = GoogleAPIUtils.getAdminDirectoryService(GoogleAPIUtils.getCredential());
		
		User user = new User();
		user.setPrimaryEmail(username);
		user.setPassword(password);
		user.setSuspended(false);
		
		UserName name = new UserName();
		name.setGivenName("Admin");
		name.setFamilyName("Admin");
		name.setFullName("Admin Admin");
		user.setName(name);
		
		@SuppressWarnings("unused")
		User userResponse = service.users().insert(user).execute();
		
		// Make the user a super admin.
		UserMakeAdmin admin = new UserMakeAdmin();
		admin.setStatus(true);
		service.users().makeAdmin(username, admin).execute();
		
		// Attach this extra data as the return payload.
		userRequest.username = username;
		userRequest.password = password;
		
		this.sendJson(resp, userRequest);
		
	}
}
