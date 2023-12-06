package org.grobid.core.analyzers;

import org.grobid.core.layout.LayoutToken;
import org.grobid.core.lang.Language;
import org.grobid.core.utilities.UnicodeUtil;
import org.junit.Before;
import org.junit.Test;

import java.util.List;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.*;

public class GrobidAnalyzerTest {
    GrobidAnalyzer target;

    @Before
    public void setUp() throws Exception {
        target = GrobidAnalyzer.getInstance();
    }

    @Test
    public void testTokenizeWithLayoutToken() {
        final List<LayoutToken> layoutTokens = target.tokenizeWithLayoutToken("This is a normal \ntext,\n\n\n on several lines.\n");

        assertThat(layoutTokens, hasSize(22));
        assertThat(layoutTokens.get(0).getText(), is("This"));
        assertThat(layoutTokens.get(1).getText(), is(" "));
        assertThat(layoutTokens.get(6).getText(), is("normal"));
        assertThat(layoutTokens.get(7).getText(), is(" "));
        assertThat(layoutTokens.get(7).isNewLineAfter(), is(true));
        assertThat(layoutTokens.get(8).getText(), is("\n"));
        assertThat(layoutTokens.get(8).isNewLineAfter(), is(false));
        assertThat(layoutTokens.get(10).getText(), is(","));
        assertThat(layoutTokens.get(10).isNewLineAfter(), is(true));
        assertThat(layoutTokens.get(11).getText(), is("\n"));
        assertThat(layoutTokens.get(11).isNewLineAfter(), is(true));
        assertThat(layoutTokens.get(12).getText(), is("\n"));
        assertThat(layoutTokens.get(12).isNewLineAfter(), is(true));
        assertThat(layoutTokens.get(13).getText(), is("\n"));
        assertThat(layoutTokens.get(13).isNewLineAfter(), is(false));
    }

    @Test
    public void testTokenizeWithLayoutToken_emptyText() {
        assertThat(target.tokenizeWithLayoutToken(""), hasSize(0));
    }

    @Test
    public void testTokenize_Korean() {
        String input = "최지수. 윤석민 (2019), 가짜뉴스 거버넌스: 정부규제, 자율규제, 공동규제 모형에 대한 비교를 중심으로, 사이버커뮤니케이션학보, 제36권 제1호, 127-180쪽.";
        input = UnicodeUtil.normaliseText(input);
        List<String> tokensStr = target.tokenize(input, new Language("kr"));
        assertThat(tokensStr, hasSize(35));

        List<LayoutToken> tokens = target.tokenizeWithLayoutToken(input, new Language("kr"));
        assertThat(tokens, hasSize(35));

        tokens = target.tokenizeWithLayoutToken(input, new Language("kr"));
        assertThat(tokens, hasSize(35));

        tokens = target.tokenizeWithLayoutToken(input, new Language("kr"));
        assertThat(tokens, hasSize(35));

        tokensStr = target.tokenize(input, new Language("kr"));
        tokensStr = target.retokenizeSubdigits(tokensStr);
        assertThat(tokensStr, hasSize(36));

        tokensStr = target.tokenize(input, new Language("kr"));
        tokens = target.retokenizeSubdigitsWithLayoutToken(tokensStr);
        assertThat(tokens, hasSize(36));

        tokens = target.tokenizeWithLayoutToken(input, new Language("kr"));
        tokens = target.retokenizeSubdigitsFromLayoutToken(tokens);
        assertThat(tokens, hasSize(36));
    }

    @Test
    public void testTokenize_Japanese() {
        String input = "오다쇼고(小田省吾), 京城尊都の 由來こ 基の 城壁に就て</title>, 朝鮮 제197호, 1931";
        input = UnicodeUtil.normaliseText(input);
        List<String> tokensStr = target.tokenize(input, new Language("jp"));
        assertThat(tokensStr, hasSize(23));

        List<LayoutToken> tokens = target.tokenizeWithLayoutToken(input, new Language("jp"));
        assertThat(tokens, hasSize(23));

        tokens = target.tokenizeWithLayoutToken(input, new Language("jp"));
        assertThat(tokens, hasSize(23));

        tokens = target.tokenizeWithLayoutToken(input, new Language("jp"));
        assertThat(tokens, hasSize(23));

        tokensStr = target.tokenize(input, new Language("jp"));
        tokensStr = target.retokenizeSubdigits(tokensStr);
        assertThat(tokensStr, hasSize(25));

        tokensStr = target.tokenize(input, new Language("jp"));
        tokens = target.retokenizeSubdigitsWithLayoutToken(tokensStr);
        assertThat(tokens, hasSize(25));

        tokens = target.tokenizeWithLayoutToken(input, new Language("jp"));
        tokens = target.retokenizeSubdigitsFromLayoutToken(tokens);
        assertThat(tokens, hasSize(25));
    }

    @Test
    public void testTokenize_Chinese() {
        String input = "郭宏奇. 中藥辨証治療灼口綜合征臨床觀察. 疾病監測与控制雜誌2009;8:484-5.";
        input = UnicodeUtil.normaliseText(input);
        List<String> tokensStr = target.tokenize(input, new Language("zh"));
        assertThat(tokensStr, hasSize(35));

        List<LayoutToken> tokens = target.tokenizeWithLayoutToken(input, new Language("zh"));
        assertThat(tokens, hasSize(35));

        tokens = target.tokenizeWithLayoutToken(input, new Language("zh"));
        assertThat(tokens, hasSize(35));

        tokens = target.tokenizeWithLayoutToken(input, new Language("zh"));
        assertThat(tokens, hasSize(35));

        tokensStr = target.tokenize(input, new Language("zh"));
        tokensStr = target.retokenizeSubdigits(tokensStr);
        assertThat(tokensStr, hasSize(35));

        tokensStr = target.tokenize(input, new Language("zh"));
        tokens = target.retokenizeSubdigitsWithLayoutToken(tokensStr);
        assertThat(tokens, hasSize(35));

        tokens = target.tokenizeWithLayoutToken(input, new Language("zh"));
        tokens = target.retokenizeSubdigitsFromLayoutToken(tokens);
        assertThat(tokens, hasSize(35));
    }
}