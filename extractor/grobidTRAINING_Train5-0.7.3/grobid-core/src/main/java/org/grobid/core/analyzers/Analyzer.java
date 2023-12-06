package org.grobid.core.analyzers;

import org.grobid.core.layout.LayoutToken;
import org.grobid.core.lang.Language;

import java.util.List;
import java.util.ArrayList;
import java.util.StringTokenizer;
	
/**
 * Abstract analyzer for tokenizing/filtering text.
 *
 */
public interface Analyzer {

	List<String> tokenize(String text);

	List<String> tokenize(String text, Language lang);

	List<String> retokenize(List<String> chunks);

	List<LayoutToken> tokenizeWithLayoutToken(String text);

    List<String> retokenizeSubdigits(List<String> chunks);

    List<LayoutToken> retokenizeSubdigitsWithLayoutToken(List<String> chunks);

    List<LayoutToken> retokenizeSubdigitsFromLayoutToken(List<LayoutToken> tokens);

	String getName();
}