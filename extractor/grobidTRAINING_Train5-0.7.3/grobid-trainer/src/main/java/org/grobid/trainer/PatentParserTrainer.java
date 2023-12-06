package org.grobid.trainer;

import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;
import java.io.*;
import java.util.*;

import org.grobid.core.GrobidModels;
import org.grobid.core.exceptions.GrobidException;
import org.grobid.core.features.FeaturesVectorReference;
import org.grobid.core.sax.MarecSaxParser;
import org.grobid.core.utilities.GrobidProperties;
import org.grobid.core.utilities.OffsetPosition;
import org.grobid.core.utilities.TextUtilities;
import org.grobid.trainer.evaluation.PatentEvaluation;

public class PatentParserTrainer extends AbstractTrainer {

    // the window value indicate the right and left context of text to consider for an annotation when building
    // the training or the test data - the value is empirically set
    // this window is used to maintain a certain level of over-sampling of the patent and NPL references, and avoid
    // to have the citation annotation too diluted because they are very rare (less than 1 token per 1000)
    private static final int trainWindow = 200;

    public PatentParserTrainer() {
        super(GrobidModels.PATENT_CITATION);
    }

    public int createTrainingData(String trainingDataDir) {
        int nb = 0;
        try {
            String path = new File(new File(getFilePath2Resources(),
                    "dataset/patent/corpus/").getAbsolutePath()).getAbsolutePath();
            createDataSet(null, path, trainingDataDir, 0);
        } catch (Exception e) {
            throw new GrobidException("An exception occurred while training Grobid.", e);
        }
        return nb;
    }

    /**
     * Add the selected features to the affiliation/address model training for
     * names
     * 
     * @param corpusDir
     *            a path where corpus files are located
     * @return the total number of used corpus items
     */
    @Override
    public int createCRFPPData(final File corpusDir, final File modelOutputPath) {
        return createCRFPPData(corpusDir, modelOutputPath, null, 1.0);
    }

    /**
     * Add the selected features to the affiliation/address model training for
     * names
     * 
     * @param corpusDir
     *            a path where corpus files are located
     * @param trainingOutputPath
     *            path where to store the temporary training data
     * @param evalOutputPath
     *            path where to store the temporary evaluation data
     * @param splitRatio
     *            ratio to consider for separating training and evaluation data, e.g. 0.8 for 80% 
     * @return the total number of used corpus items 
     */
    @Override
    public int createCRFPPData(File corpusPath, File trainingOutputPath, File evalOutputPath, double splitRatio) {
        int totalExamples = 0;
        int nbFiles = 0;
        int nbNPLRef = 0;
        int nbPatentRef = 0;
        int maxRef = 0;
        int srCitations = 0;
        int previousSrCitations = 0;
        int withSR = 0;
        try {
            System.out.println("sourcePathLabel: " + corpusPath);
            if (trainingOutputPath != null)
                System.out.println("outputPath for training data: " + trainingOutputPath);
            if (evalOutputPath != null)
                System.out.println("outputPath for evaluation data: " + evalOutputPath);

            // we convert the xml files into the usual CRF label format
            // we process all xml files in the output directory
            final File[] refFiles = corpusPath.listFiles(new FilenameFilter() {
                public boolean accept(File dir, String name) {
                    return name.endsWith(".xml");
                }
            }); 

            if (refFiles == null) {
                throw new IllegalStateException("Folder " + corpusPath.getAbsolutePath()
                        + " does not seem to contain training data. Please check");
            }

            System.out.println(refFiles.length + " xml files");

            // the file for writing the training data
            OutputStream os2 = null;
            Writer writer2 = null;
            if (trainingOutputPath != null) {
                os2 = new FileOutputStream(trainingOutputPath);
                writer2 = new OutputStreamWriter(os2, "UTF8");
            }

            // the file for writing the evaluation data
            OutputStream os3 = null;
            Writer writer3 = null;
            if (evalOutputPath != null) {
                os3 = new FileOutputStream(evalOutputPath);
                writer3 = new OutputStreamWriter(os3, "UTF8");
            }

            // get a factory for SAX parser
            SAXParserFactory spf = SAXParserFactory.newInstance();
            spf.setValidating(false);
            spf.setFeature("http://xml.org/sax/features/namespaces", false);
            spf.setFeature("http://xml.org/sax/features/validation", false);

            List<OffsetPosition> journalsPositions = null;
            List<OffsetPosition> abbrevJournalsPositions = null;
            List<OffsetPosition> conferencesPositions = null;
            List<OffsetPosition> publishersPositions = null;

            int n = 0;
            nbFiles = refFiles.length;
            for (; n < refFiles.length; n++) {
                final File xmlfile = refFiles[n];
                String name = xmlfile.getName();
                System.out.println(name);

                // Patent + NPL REF. textual data (the "all" model)
                MarecSaxParser sax = new MarecSaxParser();
                sax.patentReferences = true;
                sax.nplReferences = true;
                sax.setN(trainWindow);

                // get a new instance of parser
                final SAXParser p = spf.newSAXParser();
                p.parse(xmlfile, sax);

                nbNPLRef += sax.getNbNPLRef();
                nbPatentRef += sax.getNbPatentRef();
                if (sax.nbAllRef > maxRef) {
                    maxRef = sax.nbAllRef;
                }
                if (sax.citations != null) {
                    if (sax.citations.size() > previousSrCitations) {
                        previousSrCitations = sax.citations.size();
                        withSR++;
                    }
                }
                journalsPositions = sax.journalsPositions;
                abbrevJournalsPositions = sax.abbrevJournalsPositions;
                conferencesPositions = sax.conferencesPositions;
                publishersPositions = sax.publishersPositions;
                //totalLength += sax.totalLength;

                Writer writer = null;
                if ( (writer2 == null) && (writer3 != null) )
                        writer = writer3;
                if ( (writer2 != null) && (writer3 == null) )
                    writer = writer2;
                else {      
                    if (Math.random() <= splitRatio)
                        writer= writer2;
                    else 
                        writer = writer3;
                }

                if (sax.accumulatedText != null) {
                    String text = sax.accumulatedText.toString();
                    // add features for patent+NPL
                    addFeatures(text,
                            writer,
                            journalsPositions,
                            abbrevJournalsPositions,
                            conferencesPositions,
                            publishersPositions);
                    writer.write("\n \n");
                }
                
            }

            if (writer2 != null) {
                writer2.close();
                os2.close();
            }

            if (writer3 != null) {
                writer3.close();
                os3.close();
            }

            System.out.println("\nNumber of references: " + (nbNPLRef + nbPatentRef));
            System.out.println("Number of patent references: " + nbPatentRef);
            System.out.println("Number of NPL references: " + nbNPLRef);
            //System.out.println("Number of search report citations: " + srCitations);
            System.out.println("Average number of references: " +
                    TextUtilities.formatTwoDecimals((double) (nbNPLRef + nbPatentRef) / nbFiles));
            System.out.println("Max number of references in file: " + maxRef +"\n");

        } catch (Exception e) {
            throw new GrobidException("An exception occurred while running Grobid.", e);
        }
        return totalExamples;
    }


/*    public void train() {
        createTrainingData(GrobidProperties.getTempPath().getAbsolutePath());
//        String path = new File(new File("resources/dataset/patent/crfpp-templates/").getAbsolutePath()).getAbsolutePath();

        // train the resulting training files with features (based external command line, no JNI
        // binding for the training functions of CRF++)
        //File trainingDataPath1 = new File(GrobidProperties.getTempPath() + "/npl.train");
        //File trainingDataPath2 = new File(GrobidProperties.getTempPath() + "/patent.train");
        File trainingDataPath3 = new File(GrobidProperties.getTempPath() + "/all.train");

        // File templatePath1 = new File(getFilePath2Resources(), "dataset/patent/crfpp-templates/text.npl.references.template");
        //File templatePath2 = new File(getFilePath2Resources(), "dataset/patent/crfpp-templates/text.patent.references.template");
        File templatePath3 =
                new File(getFilePath2Resources(), "dataset/patent/crfpp-templates/text.references.template");

        GenericTrainer trainer = TrainerFactory.getTrainer(model);
        trainer.setEpsilon(GrobidProperties.getEpsilon(model));
        trainer.setWindow(GrobidProperties.getWindow(model));
        trainer.setNbMaxIterations(GrobidProperties.getNbMaxIterations(model));
        //File modelPath1 = new File(GrobidProperties.getModelPath(GrobidModels.PATENT_NPL).getAbsolutePath() + NEW_MODEL_EXT);
        //File modelPath2 = new File(GrobidProperties.getModelPath(GrobidModels.PATENT_PATENT).getAbsolutePath() + NEW_MODEL_EXT);
        File modelPath3 =
                new File(GrobidProperties.getModelPath(GrobidModels.PATENT_ALL).getAbsolutePath() + NEW_MODEL_EXT);

        //trainer.train(templatePath1, trainingDataPath1, modelPath1, GrobidProperties.getNBThreads());
        //trainer.train(templatePath2, trainingDataPath2, modelPath2, GrobidProperties.getNBThreads());
        trainer.train(templatePath3, trainingDataPath3, modelPath3, GrobidProperties.getNBThreads(), model);

        //renaming
        //renameModels(GrobidProperties.getModelPath(GrobidModels.PATENT_NPL), modelPath1);
        //renameModels(GrobidProperties.getModelPath(GrobidModels.PATENT_PATENT), modelPath2);
        renameModels(GrobidProperties.getModelPath(GrobidModels.PATENT_ALL), modelPath3);
    }
*/

    /**
     * Create the set of training and evaluation sets from the annotated examples with
     * extraction of citations in the patent description body.
     *
     * @param type type of data to be created, 0 is training data, 1 is evaluation data
     */
    public void createDataSet(String setName, String corpusPath, String outputPath, int type) {
        int nbFiles = 0;
        int nbNPLRef = 0;
        int nbPatentRef = 0;
        int maxRef = 0;
        try {
            // we use a SAX parser on the patent XML files
            MarecSaxParser sax = new MarecSaxParser();
            sax.patentReferences = true;
            sax.nplReferences = true;
            int srCitations = 0;
            int previousSrCitations = 0;
            int withSR = 0;

            List<OffsetPosition> journalsPositions = null;
            List<OffsetPosition> abbrevJournalsPositions = null;
            List<OffsetPosition> conferencesPositions = null;
            List<OffsetPosition> publishersPositions = null;

            if (type == 0) {
                // training set
                sax.setN(trainWindow);
            } else {
                // for the test set we enlarge the focus window to include all the document.
                sax.setN(-1);
            }

            // get a factory
            SAXParserFactory spf = SAXParserFactory.newInstance();
            spf.setValidating(false);
            spf.setFeature("http://xml.org/sax/features/namespaces", false);
            spf.setFeature("http://xml.org/sax/features/validation", false);

            LinkedList<File> fileList = new LinkedList<File>();
            if (setName == null) {
                fileList.add(new File(corpusPath));
            } else {
                fileList.add(new File(corpusPath));
            } 

            Writer writer = null;
            if ((setName == null) || (setName.length() == 0)) {
                writer = new OutputStreamWriter(new FileOutputStream(
                        new File(outputPath + File.separator + "all.train"), false), "UTF-8");
            } else {
                writer = new OutputStreamWriter(new FileOutputStream(
                        new File(outputPath + File.separator + "all." + setName), false), "UTF-8");
            } 

            //int totalLength = 0;
            while (fileList.size() > 0) {
                File file = fileList.removeFirst();
                if (file.isDirectory()) {
                    for (File subFile : file.listFiles()) {
                        fileList.addLast(subFile);
                    }
                } else {
                    if (file.getName().endsWith(".xml")) {
                        nbFiles++;
                        try {
                            //get a new instance of parser
                            SAXParser p = spf.newSAXParser();
                            FileInputStream in = new FileInputStream(file);
                            sax.setFileName(file.toString());
                            p.parse(in, sax);
                            //writer3.write("\n");
                            nbNPLRef += sax.getNbNPLRef();
                            nbPatentRef += sax.getNbPatentRef();
                            if (sax.nbAllRef > maxRef) {
                                maxRef = sax.nbAllRef;
                            }
                            if (sax.citations != null) {
                                if (sax.citations.size() > previousSrCitations) {
                                    previousSrCitations = sax.citations.size();
                                    withSR++;
                                }
                            }
                            journalsPositions = sax.journalsPositions;
                            abbrevJournalsPositions = sax.abbrevJournalsPositions;
                            conferencesPositions = sax.conferencesPositions;
                            publishersPositions = sax.publishersPositions;
                            //totalLength += sax.totalLength;

                            if (sax.accumulatedText != null) {
                                String text = sax.accumulatedText.toString();
                                // add features for patent+NPL
                                addFeatures(text,
                                        writer,
                                        journalsPositions,
                                        abbrevJournalsPositions,
                                        conferencesPositions,
                                        publishersPositions);
                                writer.write("\n");
                            }
                        } catch (Exception e) {
                            throw new GrobidException("An exception occured while running Grobid.", e);
                        }
                    }
                }
            }

            if (sax.citations != null) {
                srCitations += sax.citations.size();
            }
            if (setName != null) {
                System.out.println(setName + "ing on " + nbFiles + " files");
            } else {
                System.out.println("training on " + nbFiles + " files");
            }
            //System.out.println("Number of file with search report: " + withSR);
            System.out.println("Number of references: " + (nbNPLRef + nbPatentRef));
            System.out.println("Number of patent references: " + nbPatentRef);
            System.out.println("Number of NPL references: " + nbNPLRef);
            //System.out.println("Number of search report citations: " + srCitations);
            System.out.println("Average number of references: " +
                    TextUtilities.formatTwoDecimals((double) (nbNPLRef + nbPatentRef) / nbFiles));
            System.out.println("Max number of references in file: " + maxRef);

            if ((setName == null) || (setName.length() == 0)) {
                System.out.println("common data set under: " + outputPath + "/all.train");
            } else {
                System.out.println("common data set under: " + outputPath + "/all." + setName);
            }
        } catch (Exception e) {
            throw new GrobidException("An exception occurred while running Grobid.", e);
        }
    }

    public void addFeatures(String text,
                            Writer writer,
                            List<OffsetPosition> journalPositions,
                            List<OffsetPosition> abbrevJournalPositions,
                            List<OffsetPosition> conferencePositions,
                            List<OffsetPosition> publisherPositions) {
        try {
            String line;
            StringTokenizer st = new StringTokenizer(text, "\n");
            int totalLine = st.countTokens();

            int posit = 0;
            int currentJournalPositions = 0;
            int currentAbbrevJournalPositions = 0;
            int currentConferencePositions = 0;
            int currentPublisherPositions = 0;
            boolean isJournalToken;
            boolean isAbbrevJournalToken;
            boolean isConferenceToken;
            boolean isPublisherToken;
            boolean skipTest;
            while (st.hasMoreTokens()) {
                isJournalToken = false;
                isAbbrevJournalToken = false;
                isConferenceToken = false;
                isPublisherToken = false;
                skipTest = false;
                line = st.nextToken();
                if (line.trim().length() == 0) {
                    writer.write("\n");
                    posit = 0;
                    continue;
                } else if (line.endsWith("\t<ignore>")) {
                    posit++;
                    continue;
                }
                // check the position of matches for journals
                if (journalPositions != null) {
                    if (currentJournalPositions == journalPositions.size() - 1) {
                        if (journalPositions.get(currentJournalPositions).end < posit) {
                            skipTest = true;
                        }
                    }
                    if (!skipTest) {
                        for (int i = currentJournalPositions; i < journalPositions.size(); i++) {
                            if ((journalPositions.get(i).start <= posit) &&
                                    (journalPositions.get(i).end >= posit)) {
                                isJournalToken = true;
                                currentJournalPositions = i;
                                break;
                            } else if (journalPositions.get(i).start > posit) {
                                isJournalToken = false;
                                currentJournalPositions = i;
                                break;
                            }
                        }
                    }
                }
                // check the position of matches for abbreviated journals
                skipTest = false;
                if (abbrevJournalPositions != null) {
                    if (currentAbbrevJournalPositions == abbrevJournalPositions.size() - 1) {
                        if (abbrevJournalPositions.get(currentAbbrevJournalPositions).end < posit) {
                            skipTest = true;
                        }
                    }
                    if (!skipTest) {
                        for (int i = currentAbbrevJournalPositions; i < abbrevJournalPositions.size(); i++) {
                            if ((abbrevJournalPositions.get(i).start <= posit) &&
                                    (abbrevJournalPositions.get(i).end >= posit)) {
                                isAbbrevJournalToken = true;
                                currentAbbrevJournalPositions = i;
                                break;
                            } else if (abbrevJournalPositions.get(i).start > posit) {
                                isAbbrevJournalToken = false;
                                currentAbbrevJournalPositions = i;
                                break;
                            }
                        }
                    }
                }
                // check the position of matches for conferences
                skipTest = false;
                if (conferencePositions != null) {
                    if (currentConferencePositions == conferencePositions.size() - 1) {
                        if (conferencePositions.get(currentConferencePositions).end < posit) {
                            skipTest = true;
                        }
                    }
                    if (!skipTest) {
                        for (int i = currentConferencePositions; i < conferencePositions.size(); i++) {
                            if ((conferencePositions.get(i).start <= posit) &&
                                    (conferencePositions.get(i).end >= posit)) {
                                isConferenceToken = true;
                                currentConferencePositions = i;
                                break;
                            } else if (conferencePositions.get(i).start > posit) {
                                isConferenceToken = false;
                                currentConferencePositions = i;
                                break;
                            }
                        }
                    }
                }
                // check the position of matches for publishers
                skipTest = false;
                if (publisherPositions != null) {
                    if (currentPublisherPositions == publisherPositions.size() - 1) {
                        if (publisherPositions.get(currentPublisherPositions).end < posit) {
                            skipTest = true;
                        }
                    }
                    if (!skipTest) {
                        for (int i = currentPublisherPositions; i < publisherPositions.size(); i++) {
                            if ((publisherPositions.get(i).start <= posit) &&
                                    (publisherPositions.get(i).end >= posit)) {
                                isPublisherToken = true;
                                currentPublisherPositions = i;
                                break;
                            } else if (publisherPositions.get(i).start > posit) {
                                isPublisherToken = false;
                                currentPublisherPositions = i;
                                break;
                            }
                        }
                    }
                }
                FeaturesVectorReference featuresVector =
                        FeaturesVectorReference.addFeaturesPatentReferences(line,
                                totalLine,
                                posit,
                                isJournalToken,
                                isAbbrevJournalToken,
                                isConferenceToken,
                                isPublisherToken);
                if (featuresVector.label == null)
                    continue;
                writer.write(featuresVector.printVector());
                writer.flush();
                posit++;
            }
        } catch (Exception e) {
            throw new GrobidException("An exception occurred while running Grobid.", e);
        }
    }

    /**
     * Command line execution.
     *
     * @param args Command line arguments.
     * @throws Exception
     */
    public static void main(String[] args) throws Exception {
        GrobidProperties.getInstance();
        Trainer trainer = new PatentParserTrainer();
        AbstractTrainer.runTraining(trainer);
        System.out.println(AbstractTrainer.runEvaluation(trainer));
        System.exit(0);
    }

}