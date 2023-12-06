package org.grobid.core.lexicon;

import org.grobid.core.utilities.GrobidProperties;
import org.grobid.core.utilities.OffsetPosition;
import org.grobid.core.layout.LayoutToken;
import org.grobid.core.analyzers.GrobidAnalyzer;
import org.junit.*;

import java.io.File;
import java.util.Arrays;
import java.util.List;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.hasSize;
import static org.junit.Assert.assertThat;

public class FastMatcherTest {

    FastMatcher target;

    @BeforeClass
    public static void setInitialContext() throws Exception {
        GrobidProperties.getInstance();
    }

    @Before
    public void setUp() throws Exception {
        target = new FastMatcher();
    }

    @Test
    public void testFastMatcher_InitFrom_GROBID_HOME() {
        new FastMatcher(new File(
                GrobidProperties.getGrobidHomePath()
                        + "/lexicon/journals/abbrev_journals.txt"));
    }

    @Test
    public void testProcessToken_noSpace_shouldReturnToken() throws Exception {
        FastMatcher fastMatcher = new FastMatcher();

        assertThat(fastMatcher.processToken("Hebrew"), is(" Hebrew"));
    }

    @Test
    public void testProcessToken_space_shouldReturnSpace() throws Exception {
        FastMatcher fastMatcher = new FastMatcher();

        assertThat(fastMatcher.processToken(" "), is(" "));
    }

    @Test
    public void testProcessToken_newLine_shouldBeIgnored() throws Exception {
        FastMatcher fastMatcher = new FastMatcher();

        assertThat(fastMatcher.processToken("@newline"), is(""));
    }

    @Test
    public void testProcessToken_tabulation_shouldBecomeSpace() throws Exception {
        FastMatcher fastMatcher = new FastMatcher();

        assertThat(fastMatcher.processToken("\t"), is(" "));
    }

    @Test
    public void testMatcherList_location() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));
        final String input = "I'm walking in The Bronx";
        List<LayoutToken> tokenisedInput = GrobidAnalyzer.getInstance().tokenizeWithLayoutToken(input);

        final List<OffsetPosition> offsetPositions = target.matchLayoutToken(tokenisedInput);
        assertThat(offsetPositions, hasSize(2));
        assertThat(offsetPositions.get(0).start, is(8));
        assertThat(offsetPositions.get(0).end, is(10));
        assertThat(offsetPositions.get(1).start, is(10));
        assertThat(offsetPositions.get(1).end, is(10));
    }

    @Test
    public void testMatchString_location() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));

        final String input = "I'm walking in The Bronx";
        final List<OffsetPosition> positions = target.matchCharacter(input);
        assertThat(positions, hasSize(2));
        
        //The Bronx
        assertThat(positions.get(0).start, is(15));
        assertThat(positions.get(0).end, is(24));

        //Bronx
        assertThat(positions.get(1).start, is(19));
        assertThat(positions.get(1).end, is(24));
    }

    @Ignore
    @Test
    public void testMatchStringWithTag_location() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));

        final String input = "I'm walking <p> in The Bronx";
        final List<OffsetPosition> positions = target.matchCharacter(input);
        assertThat(positions, hasSize(2));

        //The Bronx
        assertThat(positions.get(0).start, is(19));
        assertThat(positions.get(0).end, is(28));

        //Bronx
        assertThat(positions.get(1).start, is(23));
        assertThat(positions.get(1).end, is(28));
    }

    @Ignore
    @Test
    public void testMatchStringOnlyTag_location_noMatch() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));

        final String input = "<p>";
        final List<OffsetPosition> positions = target.matchCharacter(input);
        assertThat(positions, hasSize(0));
    }

    @Ignore
    @Test
    public void testMatchStringAndTag_location_noMatch() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));

        final String input = "This is <p>";
        final List<OffsetPosition> positions = target.matchCharacter(input);
        assertThat(positions, hasSize(0));
    }

    @Ignore
    @Test
    public void testMatchList_location_noMatch() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));

        final String input = "This is <p>";
//        final List<OffsetPosition> offsetPositions = target.matchCharacter(Arrays.asList(input.split(" ")));
        //assertThat(offsetPositions, hasSize(0));
    }

    @Test
    public void testMatchList_location_1Match() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));

        final String input = "This is Bronx";
        List<LayoutToken> tokenisedInput = GrobidAnalyzer.getInstance().tokenizeWithLayoutToken(input);
        final List<OffsetPosition> offsetPositions = target.matchCharacterLayoutToken(tokenisedInput);
        assertThat(offsetPositions, hasSize(1));
        assertThat(offsetPositions.get(0).start, is(4));
        assertThat(offsetPositions.get(0).end, is(4));
    }

    @Test
    public void testMatchList_location_2Matches() throws Exception {
        target = new FastMatcher(this.getClass().getResourceAsStream("location.txt"));

        final String input = "This is The Bronx";
        List<LayoutToken> tokenisedInput = GrobidAnalyzer.getInstance().tokenizeWithLayoutToken(input);
        final List<OffsetPosition> offsetPositions = target.matchCharacterLayoutToken(tokenisedInput);
        assertThat(offsetPositions, hasSize(2));
        assertThat(offsetPositions.get(0).start, is(4));
        assertThat(offsetPositions.get(0).end, is(6));

        assertThat(offsetPositions.get(1).start, is(6));
        assertThat(offsetPositions.get(1).end, is(6));
    }


}
