package com.richieforeman.rapidreseller;

import java.io.IOException;
import javax.servlet.http.*;
import javax.servlet.ServletContext;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;

@SuppressWarnings("serial")
public class IndexServlet extends HttpServlet {
	public void doGet(HttpServletRequest req, HttpServletResponse resp)
			throws IOException {
		ServletContext context = getServletContext();
		InputStream is = context.getResourceAsStream("/templates/base.html");
		BufferedReader reader = new BufferedReader(new InputStreamReader(is));
		
		StringBuilder out = new StringBuilder();
		String line;
		while((line = reader.readLine()) != null) {
			out.append(line);
		}
		
		resp.setContentType("text/html");
		resp.getWriter().println(out.toString());
		reader.close();
	}
}
