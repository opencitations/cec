package org.grobid.core.sax;

import org.grobid.core.data.BiblioItem;

import java.io.*;

import org.xml.sax.*;
import org.xml.sax.helpers.*;

/**
 * SAX parser for XML crossref DOI metadata descriptions.
 * See http://www.crossref.org/openurl_info.html
 *
 * -> This is not used anymore, we use the JSON REST API from 
 *    CrossRef or from biblio-glutton, und das ist auch gut so.
 *
 */
public class CrossrefSaxParser extends DefaultHandler {

    private BiblioItem biblio;
    private String author = null;
    private CharArrayWriter text = new CharArrayWriter();

    public CrossrefSaxParser() {
    }

    public CrossrefSaxParser(BiblioItem b) {
        biblio = b;
    }

    public void characters(char[] ch, int start, int length) {
        text.reset();
        text.write(ch, start, length);
    }

    public String getText() {
        System.out.println(text.toString());
        return text.toString().trim();
    }

    public void endElement(java.lang.String uri,
                           java.lang.String localName,
                           java.lang.String qName) throws SAXException {
        System.out.println(qName);
        if (qName.equals("article_title")) {
            biblio.setArticleTitle(getText());
        }
        if (qName.equals("journal_title")) {
            biblio.setTitle(getText());
        }
        if (qName.equals("ISSN")) {
            biblio.setISSN(getText());
        }
        if (qName.equals("volume")) {
            String volume = getText();
            if (volume != null) {
                if (volume.length() > 0) {
                    biblio.setVolume(volume);
                }
            }
        }
        if (qName.equals("issue")) {
            String issue = getText();
            if (issue != null) {
                if (issue.length() > 0) {
                    biblio.setNumber(issue);
                }
            }
        }
        if (qName.equals("year")) {
            String year = getText();
            biblio.setPublicationDate(year);
            biblio.setYear(year);
        }
        if (qName.equals("first_page")) {
            String page = getText();
            if (page != null) {
                if (page.length() > 0) {
                    biblio.setBeginPage(Integer.parseInt(page));
                }
            }
        }
        if (qName.equals("contributor")) {
            biblio.addAuthor(author);
            author = null;
        }
        if (qName.equals("given_name")) {
            author = getText();
        }
        if (qName.equals("surname")) {
            author = author + " " + getText();
        }

        //biblio.setDOIRetrieval(true);
    }

    public void startElement(String namespaceURI,
                             String localName,
                             String qName,
                             Attributes atts)
            throws SAXException {
        if (qName.equals("query")) {
            String n1 = atts.getValue("status");
        }
    }

}

