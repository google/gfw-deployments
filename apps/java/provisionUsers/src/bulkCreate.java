/*
 * This assumes that you have all the necessary GData libraries
 * in your classpath, as well as the AppsForYourDomainClient sample.
 * 
 * Step 1: Update credentials
 *      2: Update CSV file location
 *      3: Compile
 *      4: Run
 */

import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import sample.appsforyourdomain.AppsForYourDomainClient;

import com.google.gdata.data.appsforyourdomain.AppsForYourDomainException;
import com.google.gdata.util.ServiceException;

public class bulkCreate extends Thread {
    static String username = "admin@domain.com";
    static String password = "password";
    static String domain = "domain.com";
    static String csvFile = "/tmp/userlist.csv";
	int numThreads = 20;
    
	AppsForYourDomainClient myClient;
	ArrayList<String[]> pool = new ArrayList<String[]>();
	
    public static void main(String args[]) throws Exception {
    	AppsForYourDomainClient client = new AppsForYourDomainClient(username, password, domain);
    	
    	bulkCreate bc = new bulkCreate(client);
    	bc.magic();
    }
    
    /*
     * Take in client and pool from main and make global.
     */
    public bulkCreate(AppsForYourDomainClient ac) {
    	myClient = ac;
    	
    	csvParser csv = new csvParser(csvFile);
    	pool = csv.getUsers();
    }

    /*
     * This is where the magic happens, duh!
     */
	public void magic() throws AppsForYourDomainException, ServiceException, IOException, InterruptedException {  
	  System.out.println("\nStarting Threads . . .\n");
	  ExecutorService threadExecutor = Executors.newFixedThreadPool(numThreads);
	  
	  Iterator<String[]> itr = pool.iterator();
	  
	  while (itr.hasNext()) {
		  String[] userInfo = itr.next();
		  
		  bulkRun br = new bulkRun(myClient);
		  br.setInfo(userInfo[0], userInfo[1], userInfo[2], userInfo[3]);
		  threadExecutor.execute( br );
		  sleep(100);
	  }
	  threadExecutor.shutdown();
    }
}
