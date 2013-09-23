import java.io.IOException;

import com.google.gdata.data.appsforyourdomain.AppsForYourDomainException;
import com.google.gdata.util.ServiceException;
import sample.appsforyourdomain.AppsForYourDomainClient;


public class bulkRun implements Runnable {
	AppsForYourDomainClient myClient;
	
	String username;
	String password;
	String firstname;
	String lastname;
	
	public bulkRun(AppsForYourDomainClient ac) {
		myClient = ac;
	}
	
	public void setInfo(String u, String p, String f, String l) {
		username = u;
		password = p;
		firstname = f;
		lastname = l;
	}
	
	public void run() {
		String userInfo = username + " " + password + " " + firstname + " " + lastname;
		System.out.println(userInfo);
		
		try {
			myClient.createUser(username, firstname, lastname, password);
		} catch (AppsForYourDomainException e) {
			e.printStackTrace();
		} catch (ServiceException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

}
