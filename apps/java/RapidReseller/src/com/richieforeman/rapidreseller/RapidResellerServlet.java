package com.richieforeman.rapidreseller;

import java.io.BufferedReader;
import java.io.IOException;

import com.google.gson.Gson;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


@SuppressWarnings("serial")
public class RapidResellerServlet extends HttpServlet {
	
	protected void sendJson(HttpServletResponse resp, Object data) throws IOException {
		resp.setContentType("text/plain");
		Gson gs = new Gson();
		resp.getWriter().println(gs.toJson(data));
	}
	
	protected String getRequestBody(HttpServletRequest req) throws IOException {
		BufferedReader reader = req.getReader();
        StringBuilder inputStringBuilder = new StringBuilder();
        
        String line = null;
		while ((line = reader.readLine()) != null) {
			inputStringBuilder.append(line);
		}
		
		return inputStringBuilder.toString();
	}
}
