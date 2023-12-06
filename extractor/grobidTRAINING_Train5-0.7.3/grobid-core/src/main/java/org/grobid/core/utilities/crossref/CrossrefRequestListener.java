package org.grobid.core.utilities.crossref;

import org.joda.time.Duration;
import java.util.List;

/**
 * Listener to catch response from a CrossrefRequest.
 *
 */
public class CrossrefRequestListener<T extends Object> {
	
	public CrossrefRequestListener() {
	}

	public CrossrefRequestListener(int rank) {
		this.rank = rank;
	}

	public static class Response<T> {
		public int status = -1;
		public List<T> results = null;
		public int interval;
		public int limitIterations;
		public long time;
		public String errorMessage;
		public Exception errorException;
		
		public Response() {
			this.status = -1;
			this.results = null;
			this.interval = 0;
			this.limitIterations = 1;
			this.time = System.currentTimeMillis();
			this.errorMessage = null;
			this.errorException = null;
		}
		
		public void setTimeLimit(String limitInterval, String limitLimit) {
			this.interval = (int)Duration.parse("PT"+limitInterval.toUpperCase()).getMillis();
			this.limitIterations = Integer.parseInt(limitLimit);
		}
		
		/*public void setException(Exception e, CrossrefRequest<T> request) {
			errorException = e;
			errorMessage = e.getClass().getName()+" thrown during request execution : "+request.toString()+"\n"+e.getMessage();
		}*/

		public void setException(Exception e, String requestString) {
			errorException = e;
			errorMessage = e.getClass().getName()+" thrown during request execution : "+requestString+"\n"+e.getMessage();
		}
		
		public int getOneStepTime() {
			return interval/limitIterations;
		}
		
		public String toString() {
			return "Response (status:"+status+" timeLimit:"+interval+"/"+limitIterations+", results:"+results.size();
		}
		
		public boolean hasError() {
			return (errorMessage != null) || (errorException != null);
		}
		
		public boolean hasResults() {
			return (results != null) && (results.size() > 0);
		}
	}
	
	/**
	 * Called when request executed and get any response
	 */
	public void onResponse(Response<T> response) {}
	
	/**
	 * Called when request succeed and response format is as expected
	 */
	public void onSuccess(List<T> results) {}
	
	/**
	 * Called when request gives an error
	 */
	public void onError(int status, String message, Exception exception) {}

	public void notify(Response<T> response) {
		
		onResponse(response);

		if (response == null) 
			System.out.println("Response is null");
		
		if (response != null && response.results != null && response.results.size() > 0)
			onSuccess(response.results);
		
		if (response.hasError()) {
			onError(response.status, response.errorMessage, response.errorException);
		}
		
		currentResponse = response;
		synchronized (this) {
			this.notifyAll();
		}
	}
	
	protected Response<T> currentResponse = null;
	/**
	 * Get response after waiting listener, usefull for synchronous call
	 */
	public Response<T> getResponse() {
		return currentResponse;
	}

	private int rank = -1;
	/**
	 * Associate the listener to a rank for identifying the response
	 */
	public int getRank() {
		return rank;
	}
}
