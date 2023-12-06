package org.grobid.core.engines.counters;

public class TableRejectionCounters {

    public static final Countable CANNOT_PARSE_LABEL_TO_INT = new Countable() {
        @Override
        public String getName() {
            return "CANNOT_PARSE_LABEL_TO_INT";
        }
    };

    public static final Countable HEADER_NOT_STARTS_WITH_TABLE_WORD = new Countable() {
        @Override
        public String getName() {
            return "HEADER_NOT_STARTS_WITH_TABLE_WORD";
        }
    };

    public static final Countable HEADER_AND_CONTENT_INTERSECT = new Countable() {
        @Override
        public String getName() {
            return "HEADER_AND_CONTENT_INTERSECT";
        }
    };

    public static final Countable HEADER_AREA_BIGGER_THAN_CONTENT = new Countable() {
        @Override
        public String getName() {
            return "HEADER_NOT_STARTS_WITH_TABLE_WORD";
        }
    };

    public static final Countable CONTENT_SIZE_TOO_SMALL = new Countable() {
        @Override
        public String getName() {
            return "CONTENT_SIZE_TOO_SMALL";
        }
    };

    public static final Countable CONTENT_WIDTH_TOO_SMALL = new Countable() {
        @Override
        public String getName() {
            return "CONTENT_WIDTH_TOO_SMALL";
        }
    };

    public static final Countable FEW_TOKENS_IN_HEADER = new Countable() {
        @Override
        public String getName() {
            return "FEW_TOKENS_IN_HEADER";
        }
    };

    public static final Countable FEW_TOKENS_IN_CONTENT = new Countable() {
        @Override
        public String getName() {
            return "FEW_TOKENS_IN_CONTENT";
        }
    };

    public static final Countable EMPTY_LABEL_OR_HEADER_OR_CONTENT = new Countable() {
        @Override
        public String getName() {
            return "EMPTY_LABEL_OR_HEADER_OR_CONTENT";
        }
    };

    public static final Countable HEADER_AND_CONTENT_DIFFERENT_PAGES = new Countable() {
        @Override
        public String getName() {
            return "HEADER_AND_CONTENT_DIFFERENT_PAGES";
        }
    };

    public static final Countable HEADER_NOT_CONSECUTIVE = new Countable() {
        @Override
        public String getName() {
            return "HEADER_NOT_CONSECUTIVE";
        }
    };

}
