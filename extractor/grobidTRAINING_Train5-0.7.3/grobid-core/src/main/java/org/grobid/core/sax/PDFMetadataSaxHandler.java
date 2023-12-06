package org.grobid.core.sax;

import org.grobid.core.document.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;
import org.grobid.core.data.Metadata;

/**
 * SAX parser for the metadata of PDF files obtained via xpdf pdfalto.
 *
 */
public class PDFMetadataSaxHandler extends DefaultHandler {
	public static final Logger LOGGER = LoggerFactory.getLogger(PDFMetadataSaxHandler.class);

    private StringBuilder accumulator = new StringBuilder(); // Accumulate parsed text

	private Document doc = null;

    private Metadata metadata = null;

    public void characters(char[] ch, int start, int length) {
        accumulator.append(ch, start, length);
    }

    public String getText() {
        String res = accumulator.toString().trim();
        return res.trim();
    }

	public PDFMetadataSaxHandler(Document d) {
		doc = d;
        metadata = new Metadata();
	}
	public void endElement(String uri, String localName,
			String qName) throws SAXException {

		if (qName.equals("METADATA")) {
		} else if (qName.equals("TITLE")) {
		    metadata.setTitle(getText());
			accumulator.setLength(0);
		} else if (qName.equals("SUBJECT")) {
            metadata.setSubject(getText());
            accumulator.setLength(0);
		} else if (qName.equals("KEYWORDS")) {
            metadata.setKeywords(getText());
            accumulator.setLength(0);
        } else if (qName.equals("AUTHOR")) {
            metadata.setAuthor(getText());
            accumulator.setLength(0);
        } else if (qName.equals("CREATOR")) {
            metadata.setCreator(getText());
            accumulator.setLength(0);
        } else if (qName.equals("PRODUCER")) {
            metadata.setProducer(getText());
            accumulator.setLength(0);
        } else if (qName.equals("CREATIONDATE")) {
            metadata.setCreateDate(getText());
            accumulator.setLength(0);
        } else if (qName.equals("MODIFICATIONDATE")) {
            metadata.setModificationDate(getText());
            accumulator.setLength(0);
        }

	}

	public void endDocument(){
	}

	public void startElement(String namespaceURI, String localName,
			String qName, Attributes atts) throws SAXException {

        if (qName.equals("METADATA")) {
        } else if (qName.equals("TITLE")) {
        } else if (qName.equals("SUBJECT")) {
        } else if (qName.equals("KEYWORDS")) {
        } else if (qName.equals("AUTHOR")) {
        } else if (qName.equals("CREATOR")) {
        } else if (qName.equals("PRODUCER")) {
        } else if (qName.equals("CREATIONDATE")) {
        } else if (qName.equals("MODIFICATIONDATE")) {

        }
    }

    public Metadata getMetadata(){
        return metadata;
    }
}

