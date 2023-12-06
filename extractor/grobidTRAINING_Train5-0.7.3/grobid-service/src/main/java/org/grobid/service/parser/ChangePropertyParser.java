package org.grobid.service.parser;

import org.grobid.core.exceptions.GrobidPropertyException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.IOException;
import java.io.StringReader;

public class ChangePropertyParser {

    Document doc;

    /**
     * Constructor of ChangePropertyParser.
     *
     * @param pInput the xml to parse.
     * @throws ParserConfigurationException
     * @throws SAXException
     * @throws IOException
     */
    public ChangePropertyParser(String pInput) {
        try {
            DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder dBuilder = null;
            dBuilder = dbFactory.newDocumentBuilder();
            doc = dBuilder.parse(new InputSource(new StringReader(pInput)));
            doc.getDocumentElement().normalize();
        } catch (ParserConfigurationException | SAXException | IOException e) {
            throw new GrobidPropertyException("Error while manipulating the grobid properties. ", e);
        }
    }

    public String getPassword() {
        return getValue("password");
    }

    public String getKey() {
        return getValue("key");
    }

    public String getValue() {
        return getValue("value");
    }

    public String getType() {
        return getValue("type");
    }

    /**
     * Return the value of the pTag.
     *
     * @param pTag the tag name.
     * @return the value contained in the tag.
     */
    protected String getValue(String pTag) {
        NodeList nList = doc.getElementsByTagName("changeProperty");

        for (int temp = 0; temp < nList.getLength(); temp++) {
            Node nNode = nList.item(temp);
            if (nNode.getNodeType() == Node.ELEMENT_NODE) {
                Element eElement = (Element) nNode;
                return getTagValue(pTag, eElement);
            }
        }
        return null;
    }

    /**
     * Return the value of the tag pTag in element eElement
     *
     * @param sTag     the tag name.
     * @param eElement the element
     * @return the value contained in the tag.
     */
    protected static String getTagValue(String sTag, Element eElement) {
        NodeList nlList = eElement.getElementsByTagName(sTag).item(0)
                .getChildNodes();

        Node nValue = (Node) nlList.item(0);

        return nValue.getNodeValue();
    }

}
