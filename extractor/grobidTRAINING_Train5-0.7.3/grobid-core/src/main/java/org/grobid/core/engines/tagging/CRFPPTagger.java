package org.grobid.core.engines.tagging;

import com.google.common.base.Splitter;
import org.chasen.crfpp.Model;
import org.chasen.crfpp.Tagger;
import org.grobid.core.GrobidModel;
import org.grobid.core.engines.ModelMap;
import org.grobid.core.exceptions.GrobidException;
import org.grobid.core.exceptions.GrobidExceptionStatus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

public class CRFPPTagger implements GenericTagger {
    public static final Logger LOGGER = LoggerFactory.getLogger(CRFPPTagger.class);
    private final Model model;

    public CRFPPTagger(GrobidModel model) {
        this.model = ModelMap.getModel(model);
    }

    @Override
    public String label(Iterable<String> data) {
        return getTaggerResult(data, null);
    }


    protected String getTaggerResult(Iterable<String> st, String type) {
        Tagger tagger = null;
        StringBuilder res;
        try {
            tagger = feedTaggerAndParse(st);

            res = new StringBuilder();
            for (int i = 0; i < tagger.size(); i++) {
                for (int j = 0; j < tagger.xsize(); j++) {
                    res.append(tagger.x(i, j)).append("\t");
                }

                if (type != null) {
                    res.append(type).append("\t");
                }

                res.append(tagger.y2(i));
                res.append("\n");
            }
        } finally {
            if (tagger != null) {
                tagger.delete();
            }
        }

        return res.toString();
    }

    @Override
    public String label(String data) {
        return label(Splitter.on("\n").split(data));
    }

    @Override
    public void close() throws IOException {

    }

    private Tagger feedTaggerAndParse(Iterable<String> st) {
        Tagger tagger = getNewTagger();
        feedTaggerAndParse(tagger, st);
        return tagger;
    }

//	protected void feedTagger(StringTokenizer st) {
//        Tagger tagger = getNewTagger();
//		feedTagger(tagger, st);
//        tagger.delete();
//	}

    public Tagger getNewTagger() {
        return model.createTagger();
    }


    public static void feedTaggerAndParse(Tagger tagger, Iterable<String> st) {
        tagger.clear();
        feedTagger(tagger, st);
        if (!tagger.parse()) {
            throw new GrobidException("CRF++ tagging failed!", GrobidExceptionStatus.TAGGING_ERROR);
        }

        if (!tagger.what().isEmpty()) {
            LOGGER.warn("CRF++ Tagger Warnings: " + tagger.what());
        }
    }

    private static void feedTagger(Tagger tagger, Iterable<String> st) {
        for (String piece : st) {
            if (piece.trim().isEmpty()) {
                continue;
            }
            if (!tagger.add(piece)) {
                LOGGER.warn("CRF++ Tagger Warnings: " + tagger.what());
                throw new GrobidException("Cannot add a feature row: " + piece
                        + "\n Reason: " + tagger.what());
            }
        }
    }

}
