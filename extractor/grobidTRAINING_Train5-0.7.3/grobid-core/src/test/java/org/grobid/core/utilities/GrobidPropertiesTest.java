package org.grobid.core.utilities;

import org.apache.commons.lang3.StringUtils;
import org.grobid.core.GrobidModel;
import org.grobid.core.GrobidModels;
import org.grobid.core.engines.tagging.GrobidCRFEngine;
import org.grobid.core.exceptions.GrobidPropertyException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.Ignore;    

import java.io.File;
import java.io.IOException;
import java.util.Collections;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

@Ignore
public class GrobidPropertiesTest {
    @Before
    public void setUp() {
        GrobidProperties.getInstance();
    }

    @After
    public void tearDown() throws Exception {
        GrobidProperties.reset();
    }

    @Test(expected = GrobidPropertyException.class)
    public void testSet_GROBID_HOME_PATH_NullPath_shouldThrowException() {
        GrobidProperties.setGrobidHome(null);
    }

    @Test(expected = GrobidPropertyException.class)
    public void testSet_GROBID_HOME_PATH_FileNotExisting_shouldThrowException() {
        GrobidProperties.setGrobidHome("/NotExistingPath");
    }

    @Test
    public void testNativeLibraryPath() throws IOException {
//        File expectedFile = new File(MockContext.GROBID_HOME_PATH
//                + File.separator + "/lib");
        assertNotNull(GrobidProperties
                .getNativeLibraryPath().getCanonicalFile());
    }

    @Test
    public void testgetsetNativeLibraryPath() {
        String value = "value";
        GrobidProperties.setNativeLibraryPath(value);
        assertEquals("The parameter has not the value expected", value,
                GrobidProperties.getNativeLibraryPath().getPath());
    }

    @Test
    public void testsetgetProxyHost() {
        String value = "host";
        GrobidProperties.setProxyHost(value);
        assertEquals("The parameter has not the value expected", value,
                GrobidProperties.getProxyHost());
    }

    @Test
    public void testsetgetProxyPort() {
        int value = 1;
        GrobidProperties.setProxyPort(value);
        assertEquals("The parameter has not the value expected", value,
                GrobidProperties.getProxyPort().intValue());
    }

    @Test
    public void testsetgetWapitiNbThreads() {
        int value = 1;
        GrobidProperties.setWapitiNbThreads(value);
        assertEquals("The parameter has not the value expected", value,
                GrobidProperties.getWapitiNbThreads().intValue());
    }

    @Test
    public void testgetNBThreadsShouldReturnAvailableProcessorsIfZero() {
        int value = 0;
        GrobidProperties.setWapitiNbThreads(value);
        assertEquals("The parameter has not the value expected",
                String.valueOf(Runtime.getRuntime().availableProcessors()),
                GrobidProperties.getWapitiNbThreads());
        assertTrue("The parameter is not greater than zero",
            GrobidProperties.getWapitiNbThreads().intValue() > 0);
    }

    @Test
    public void testShouldReturnModelPathWithExtension() {
        GrobidModels model = GrobidModels.DATE;
        String extension = GrobidProperties.getGrobidCRFEngine(model).getExt();
        assertEquals(
            "model path for " + model.name(),
            new File(GrobidProperties.getGrobidHome(),
                GrobidProperties.FOLDER_NAME_MODELS
                + File.separator
                + model.getFolderName()
                + File.separator
                + GrobidProperties.FILE_NAME_MODEL
                + "."
                + extension
            ).getAbsoluteFile(),
            GrobidProperties.getModelPath(model).getAbsoluteFile()
        );
    }

    @Test
    public void testgetLanguageDetectorFactory() {
        assertEquals("The parameter has not the value expected",
                "org.grobid.core.lang.impl.CybozuLanguageDetectorFactory",
                GrobidProperties.getLanguageDetectorFactory());
    }

    @Test
    public void testgetPdfaltoPath() throws Exception {
        assertNotNull("The parameter has not the value expected", GrobidProperties
                .getPdfaltoPath().getAbsolutePath());
    }

    @Test
    public void testGetInstance() throws Exception {
        GrobidProperties.reset();
        GrobidProperties.getInstance();
        // test the resue of the instance created previously
        GrobidProperties.reset();
        assertTrue("GrobidProperties.getInstance() does not return an instance of GrobidProperties",
                GrobidProperties.getInstance() != null);
    }

}
