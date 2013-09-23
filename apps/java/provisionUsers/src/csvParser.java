/*
 * CSV Format: username,password,firstname,lastname
 * 
 */

import java.io.*;
import java.util.*;
import java.util.regex.*;

public class csvParser {
	ArrayList<String[]> pool = new ArrayList<String[]>();

	  public static void main(String[] args) {
		  	csvParser csv = new csvParser("/tmp/userlist.csv");
	  }
	  
	  public csvParser (String filename) {
		    File file = new File("/tmp/userlist.csv");
		    FileInputStream fis = null;
		    BufferedInputStream bis = null;
		    DataInputStream dis = null;

		    try {
		      fis = new FileInputStream(file);

		      // Here BufferedInputStream is added for fast reading.
		      bis = new BufferedInputStream(fis);
		      dis = new DataInputStream(bis);

		      // dis.available() returns 0 if the file does not have more lines.
		      while (dis.available() != 0) {
		        String readLine = dis.readLine();
		        
				String[] x = Pattern.compile(",").split(readLine);
				addUser(x[0], x[1], x[2], x[3]);
		      }

		      // dispose all the resources after using them.
		      fis.close(); bis.close(); dis.close();

		    } catch (FileNotFoundException e) {
		      e.printStackTrace();
		    } catch (IOException e) {
		      e.printStackTrace();
		    }
	  }
	  
	  public void addUser(String username, String password, String first, String last) {
			String[] userInfo = new String[]{username, password, first, last};
			pool.add(userInfo);
	  }
	  
	  public ArrayList<String[]> getUsers() {
		  	return pool;
	  }
}
