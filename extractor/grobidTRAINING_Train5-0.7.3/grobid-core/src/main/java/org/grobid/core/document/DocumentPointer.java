package org.grobid.core.document;

import com.google.common.base.Preconditions;
import com.google.common.primitives.Ints;

/**
 * Class representing a pointer within a PDF document, basically a block index and then a token index within a block (not global token index)
 */
public class DocumentPointer implements Comparable<DocumentPointer>{
    public static final DocumentPointer START_DOCUMENT_POINTER = new DocumentPointer(0, 0 , 0);


    private final int blockPtr;
    private final int tokenBlockPos;
    private final int tokenDocPos;

    public DocumentPointer(int blockPtr, int tokenDocPos, int tokenBlockPos) {
        Preconditions.checkArgument(tokenDocPos >= tokenBlockPos);
        Preconditions.checkArgument(tokenBlockPos >= 0);
        this.tokenDocPos = tokenDocPos;
        this.tokenBlockPos = tokenBlockPos;
        this.blockPtr = blockPtr;
    }

    public DocumentPointer(Document doc, int blockIndex, int tokenDocPos) {
        this(blockIndex, tokenDocPos, tokenDocPos - doc.getBlocks().get(blockIndex).getStartToken());
    }

    @Override
    public int compareTo(DocumentPointer o) {
        return Ints.compare(tokenDocPos, o.tokenDocPos);
    }

    public int getBlockPtr() {
        return blockPtr;
    }

    public int getTokenBlockPos() {
        return tokenBlockPos;
    }

    public int getTokenDocPos() {
        return tokenDocPos;
    }

    @Override
    public String toString() {
        return "DocPtr(Block No: " + blockPtr + "; Token position in block: " + tokenBlockPos + "; position of token in doc: " + tokenDocPos + ")";
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;

        DocumentPointer that = (DocumentPointer) o;

        if (blockPtr != that.blockPtr) return false;
        if (tokenBlockPos != that.tokenBlockPos) return false;
        if (tokenDocPos != that.tokenDocPos) return false;

        return true;
    }

    @Override
    public int hashCode() {
        int result = blockPtr;
        result = 31 * result + tokenBlockPos;
        result = 31 * result + tokenDocPos;
        return result;
    }
}
