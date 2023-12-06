package org.grobid.core.sax;

import org.grobid.core.exceptions.GrobidException;
import org.grobid.core.utilities.TextUtilities;
import org.grobid.core.lexicon.Lexicon;
import org.grobid.core.utilities.OffsetPosition;
import org.grobid.core.analyzers.GrobidAnalyzer;

import org.xml.sax.*;
import org.xml.sax.helpers.*;

import java.util.*;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * SAX parser initially made for XML CLEF IP data (collection, training and topics).
 * But it works also fine for parsing ST.36 stuff as the formats are similar.
 *
 */
public class MarecSaxParser extends DefaultHandler {
	public static final Logger LOGGER = LoggerFactory.getLogger(MarecSaxParser.class);

    private StringBuffer accumulator = new StringBuffer(); // Accumulate parsed text
    private StringBuffer accumulatorRef = new StringBuffer(); // Accumulate parsed text

    private String PatentNumber = null;
    private int PatentID = -1;
    private String PublicDate = null;
    private String PriorityDate = null;
    private String CodeType = null;
    private String PublicationDate = null;
    private String Content = null;
    private List<String> CitedPatentNumber = null;
    private List<Integer> CitationID = null;
    private String Classification = null;

    // working variables
    private String cited_number = null;
	
    public Map<String, ArrayList<String>> referencesPatent = null;
    public List<String> referencesNPL = null;
    public List<String> citations = null; // search report citations

    private boolean npl = false; // indicate if the current reference is to patent or to a npl
    private boolean ref = false; // are we reading a ref?

    private boolean refFound = false;

    private int nbNPLRef = 0;
    private int nbPatentRef = 0;
    public int nbAllRef = 0;

    private int N = -1;  // window of text to be output around the reference strings
	// value at -1 means no window considered - everything will be outputed
	
    public boolean patentReferences = false;
    public boolean nplReferences = false;

    private String currentFileName = null;
    public Lexicon lexicon = Lexicon.getInstance();

    public List<OffsetPosition> journalsPositions = null;
    public List<OffsetPosition> abbrevJournalsPositions = null;
    public List<OffsetPosition> conferencesPositions = null;
    public List<OffsetPosition> publishersPositions = null;

    public StringBuffer accumulatedText = null;
    private StringBuffer allContent = null;
	
	private GrobidAnalyzer analyzer = GrobidAnalyzer.getInstance(); 

    public MarecSaxParser() {
    }

    public void setN(int n) {
        N = n;
    }

    public void characters(char[] buffer, int start, int length) {
        if (ref) {
            accumulatorRef.append(buffer, start, length);
        } else {
            accumulator.append(buffer, start, length);
        }
    }

    public String getText() {
        //System.out.println(accumulator.toString().trim());
        return accumulator.toString().trim();
    }

    public int getNbNPLRef() {
        return nbNPLRef;
    }

    public int getNbPatentRef() {
        return nbPatentRef;
    }

    public String getRefText() {
        //System.out.println(accumulator.toString().trim());
        return accumulatorRef.toString().trim();
    }

    public void setFileName(String name) {
        currentFileName = name;
        if (referencesPatent == null) {
            referencesPatent = new HashMap<String, ArrayList<String>>();
        }
        referencesPatent.put(name, new ArrayList<String>());
    }

    public void endElement(java.lang.String uri,
                           java.lang.String localName,
                           java.lang.String qName) throws SAXException {
        if (qName.equals("date")) {
            accumulator.setLength(0);
        } 
		else if (qName.equals("ref") || qName.equals("bibl")) {
            String refString = getRefText();
            refString = refString.replace("\n", " ");
            refString = refString.replace("\t", " ");
            refString = refString.replace("  ", " ");

            if (npl && ref) {
                if (referencesNPL == null)
                    referencesNPL = new ArrayList<String>();
                referencesNPL.add(refString);
                refFound = true;
                if (nplReferences)
                    nbNPLRef++;
            } else if (ref) {
                if (referencesPatent == null) {
                    referencesPatent = new HashMap<String, ArrayList<String>>();
                }
                ArrayList<String> refss = referencesPatent.get(currentFileName);

                if (refss == null) {
                    refss = new ArrayList<String>();
                }

                refss.add(refString);
                referencesPatent.put(currentFileName, refss);
                refFound = true;
                if (patentReferences) {
                    nbPatentRef++;
                }
            }

            if (refFound) {
                // we tokenize the text
                //ArrayList<String> tokens = TextUtilities.segment(refString, "[("+TextUtilities.punctuations);
                //StringTokenizer st = new StringTokenizer(refString, delimiters, true);
				List<String> tokenizations = new ArrayList<String>();
				try {
					// TBD: pass a language object to the tokenize method call 
					tokenizations = analyzer.tokenize(refString);
				}
				catch(Exception e) {
					LOGGER.debug("Tokenization for XML patent document has failed.");
				}
				
                int i = 0;
                //String token = null;
                //for(String token : tokens) {
                //while (st.hasMoreTokens()) {
				for(String token : tokenizations) {	
                    //token = st.nextToken().trim();
	                if ( (token.trim().length() == 0) || 
						 (token.equals(" ")) || 
					     (token.equals("\t")) || 
						 (token.equals("\n")) ||
						 (token.equals("\r"))
						 ) {
                        continue;
                    }
                    try {
                        accumulatedText.append(token + "\t");
                        allContent.append(token + " ");
                        if (npl) {
                            if (nplReferences) {
                                if (i == 0) {
                                    //accumulatedText.append("refNPLBegin\n");
                                    accumulatedText.append("I-<refNPL>\n");
                                } else if (token == null) {
                                    //accumulatedText.append("refNPLEnd\n");
                                    accumulatedText.append("E-<refNPL>\n");
                                } else {
                                    accumulatedText.append("<refNPL>\n");
                                }
                            } else
                                accumulatedText.append("<other>\n");
                        } else {
                            if (patentReferences) {
                                if (i == 0)
                                    accumulatedText.append("I-<refPatent>\n");
                                else if (token == null)
                                    accumulatedText.append("E-<refPatent>\n");
                                else
                                    accumulatedText.append("<refPatent>\n");
                            } else
                                accumulatedText.append("<other>\n");
                        }
                    } catch (Exception e) {
//						e.printStackTrace();
                        throw new GrobidException("An exception occured while running Grobid.", e);
                    }
                    i++;
                }
            }
            ref = false;
        } else if (qName.equals("classification-ipcr")) {
            accumulator.setLength(0);
        } else if (qName.equals("classification-symbol")) {
            accumulator.setLength(0);
        } else if (qName.equals("abstract")) {
            accumulator.setLength(0);
        } else if (qName.equals("heading")) {
            accumulator.append(" ");
        } else if (qName.equals("description")) {
            if (refFound) {
                String content = getText();

                // we tokenize the text
                //ArrayList<String> tokens = TextUtilities.segment(content, "[("+TextUtilities.punctuations);
                //StringTokenizer st = new StringTokenizer(content, delimiters, true);
				List<String> tokenizations = new ArrayList<String>();
				try {
					// TBD: pass a language object to the tokenize method call 
					tokenizations = analyzer.tokenize(content);	
				}
				catch(Exception e) {
					LOGGER.debug("Tokenization for XML patent document has failed.");
				}

                int i = 0;
                //String token = null;
                //for(String token : tokens) {
                //while (st.hasMoreTokens()) {
				for(String token : tokenizations) {	
                    //token = st.nextToken().trim();
	                if ( (token.trim().length() == 0) || 
						 (token.equals(" ")) || 
					     (token.equals("\t")) || 
						 (token.equals("\n")) ||
						 (token.equals("\r"))
						 ) {
                        continue;
                    }
                    // we print only a window of N words
                    if ( (i > N) && (N != -1) ) {
                        //break;
                        token = token.trim();
                        if (token.length() > 0) {
                            accumulatedText.append(token + "\t" + "<ignore>\n");
                            allContent.append(token + " ");
                        }
                    } else {
                        try {
                            token = token.trim();
                            if (token.length() > 0) {
                                accumulatedText.append(token + "\t" + "<other>\n");
                                allContent.append(token + " ");
                            }
                        } catch (Exception e) {
                            throw new GrobidException("An exception occured while running Grobid.", e);
                        }
                    }
                    i++;
                }

                accumulator.setLength(0);
                refFound = false;
            }
        } else if (qName.equals("patcit")) {
            // we register the citation, the citation context will be marked in a later stage
            if (citations == null)
                citations = new ArrayList<String>();
            citations.add(cited_number);
            accumulator.setLength(0);
        } else if (qName.equals("invention-title")) {
            accumulator.setLength(0);
        } else if (qName.equals("applicants")) {
            accumulator.setLength(0);
        } else if (qName.equals("inventors")) {
            accumulator.setLength(0);
        } else if (qName.equals("document-id")) {
            accumulator.setLength(0);
        } else if (qName.equals("legal-status")) {
            accumulator.setLength(0);
        } else if (qName.equals("bibliographic-data")) {
            accumulator.setLength(0);
        } else if (qName.equals("doc-number")) {
            accumulator.setLength(0);
        } else if (qName.equals("country")) {
            accumulator.setLength(0);
        } else if (qName.equals("kind")) {
            accumulator.setLength(0);
        } else if (qName.equals("classification-symbol")) {
            accumulator.setLength(0);
        } else if (qName.equals("classification-ecla")) {
            accumulator.setLength(0);
        } else if (qName.equals("patent-document") || qName.equals("fulltext-document")) {
            String allString = allContent.toString();
            journalsPositions = lexicon.tokenPositionsJournalNames(allString);
            abbrevJournalsPositions = lexicon.tokenPositionsAbbrevJournalNames(allString);
            conferencesPositions = lexicon.tokenPositionsConferenceNames(allString);
            publishersPositions = lexicon.tokenPositionsPublisherNames(allString);
            allContent = null;
            allString = null;
        } else if (qName.equals("row")) {
            accumulator.append(" ");
        } else if (qName.equals("p")) {
            accumulator.append("\n");
        }
    }

    public void startElement(String namespaceURI,
                             String localName,
                             String qName,
                             Attributes atts) throws SAXException {
        if (qName.equals("patent-document") || qName.equals("fulltext-document")) {
            nbNPLRef = 0;
            nbPatentRef = 0;
            nbAllRef = 0;
            int length = atts.getLength();

            // Process each attribute
            for (int i = 0; i < length; i++) {
                // Get names and values for each attribute
                String name = atts.getQName(i);
                String value = atts.getValue(i);

                if (name != null) {
                    if (name.equals("lang")) {
                        //Global_Language_Code = value.toLowerCase();
                    }
                    if (name.equals("doc-number")) {
                        PatentNumber = "EP" + value;
                    }
                    if (name.equals("kind")) {
                        CodeType = value;
                    }
                    if (name.equals("date")) {
                        PublicDate = value;
                    }
                }
            }

            CitedPatentNumber = new ArrayList<String>();
            accumulatedText = new StringBuffer();
            allContent = new StringBuffer();
            accumulator.setLength(0);
        } else if (qName.equals("description")) {
            accumulator.setLength(0);
        } else if (qName.equals("ref") || qName.equals("bibl")) {
            int length = atts.getLength();
            nbAllRef++;
            // Process each attribute
            for (int i = 0; i < length; i++) {
                // Get names and values for each attribute
                String name = atts.getQName(i);
                String value = atts.getValue(i);

                if (name != null) {
                    if (name.equals("type") || name.equals("typ")) {
                        if (value.equals("npl") || value.equals("book") || value.equals("journal")) {
                            String content = getText();

                            // we output what has been read so far in the description
                            // we tokenize the text
                            //ArrayList<String> tokens =
                            //StringTokenizer st = new StringTokenizer(content, delimiters, true);
							List<String> tokenizations = new ArrayList<String>();
							try {
								// TBD: pass a language object to the tokenize method call 
								tokenizations = analyzer.tokenize(content);		
							}
							catch(Exception e) {
								LOGGER.debug("Tokenization for XML patent document has failed.");
							}

                            //int nbTokens = st.countTokens();
							int nbTokens = tokenizations.size();
                            int j = 0;
                            //while (st.hasMoreTokens()) {
							for(String token : tokenizations) {	
                                //String token = st.nextToken().trim();
				                if ( (token.trim().length() == 0) || 
									 (token.equals(" ")) || 
								     (token.equals("\t")) || 
									 (token.equals("\n")) ||
									 (token.equals("\r"))
									 ) {
                                    continue;
                                }

                                if ((j > (nbTokens - N) && (N != -1)) || (refFound && (j < N) && (N != -1))) {
                                    try {
                                        accumulatedText.append(token + "\t" + "<other>\n");
                                        allContent.append(token + " ");
                                    } catch (Exception e) {
//										e.printStackTrace();
                                        throw new GrobidException(
                                                "An exception occured while running Grobid.", e);
                                    }
                                } else {
                                    try {
                                        accumulatedText.append(token + "\t" + "<ignore>\n");
                                        allContent.append(token + " ");
                                    } catch (Exception e) {
//										e.printStackTrace();
                                        throw new GrobidException(
                                                "An exception occured while running Grobid.", e);
                                    }
                                }
                                j++;
                            }

                            accumulator.setLength(0);

                            npl = true;
                            ref = true;
                        } else if (value.equals("patent") || value.equals("pl")) {
                            String content = getText();

                            // we output what has been read so far in the description
                            // we tokenize the text
                            //ArrayList<String> tokens =
                            //	TextUtilities.segment(content,"[("+TextUtilities.punctuations);
                            //StringTokenizer st = new StringTokenizer(content, delimiters, true);
							List<String> tokenizations = new ArrayList<String>();
							try {
								// TBD: pass a language object to the tokenize method call 
								tokenizations = analyzer.tokenize(content);		
							}
							catch(Exception e) {
								LOGGER.debug("Tokenization for XML patent document has failed.");
							}
							
                            //int nbTokens = st.countTokens();
							int nbTokens = tokenizations.size();
                            int j = 0;
							for(String token : tokenizations) {
                            	//while (st.hasMoreTokens()) {
                                //String token = st.nextToken().trim();
				                if ( (token.trim().length() == 0) || 
									 (token.equals(" ")) || 
								     (token.equals("\t")) || 
									 (token.equals("\n")) ||
									 (token.equals("\r"))
									 ) {
                                    continue;
                                }

                                if ((j > (nbTokens - N)) | (refFound & (j < N))) {
                                    try {
                                        accumulatedText.append(token + "\t" + "<other>\n");
                                        allContent.append(token + " ");
                                    } catch (Exception e) {
//										e.printStackTrace();
                                        throw new GrobidException(
                                                "An exception occured while running Grobid.", e);
                                    }
                                } else {
                                    try {
                                        accumulatedText.append(token + "\t" + "<ignore>\n");
                                        allContent.append(token + " ");
                                    } catch (Exception e) {
//										e.printStackTrace();
                                        throw new GrobidException(
                                                "An exception occured while running Grobid.", e);
                                    }
                                }
                                j++;
                            }

                            accumulator.setLength(0);
                            npl = false;
                            ref = true;
                        } else {
                            System.out.println("Warning: unknown attribute value for ref or bibl: " + value);
                            ref = false;
                            npl = false;
                        }
                    }
                }
            }

            accumulatorRef.setLength(0);
        } else if (qName.equals("claim")) {
            accumulator.setLength(0);
        } else if (qName.equals("invention-title")) {
            accumulator.setLength(0);
        } else if (qName.equals("patcit")) {
            int length = atts.getLength();

            // Process each attribute
            for (int i = 0; i < length; i++) {
                // Get names and values for each attribute
                String name = atts.getQName(i);
                String value = atts.getValue(i);

                if (name != null) {
                    if (name.equals("ucid")) {
                        cited_number = value;
                        // we normally need to normalize a little bit this patent nummer
                    }
                }
            }
        }
    }

}