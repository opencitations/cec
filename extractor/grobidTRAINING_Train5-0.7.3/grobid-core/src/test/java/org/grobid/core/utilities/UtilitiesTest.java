package org.grobid.core.utilities;

import java.io.File;
import java.io.IOException;

import java.util.List;
import java.util.ArrayList;

import org.junit.Test;
import static org.junit.Assert.*;

public class UtilitiesTest {

	@Test
	public void testStringToBooleanTrue() {
		assertEquals(
				"stringToBoolean value does not match expected result", true,
				Utilities.stringToBoolean("true"));
	}

	@Test
	public void testStringToBooleanTrue2() {
		assertEquals(
				"stringToBoolean value does not match expected result", true,
				Utilities.stringToBoolean(" TruE "));
	}

	@Test
	public void testStringToBooleanFalse() {
		assertEquals(
				"stringToBoolean value does not match expected result", false,
				Utilities.stringToBoolean("false"));
	}

	@Test
	public void testStringToBooleanFalse2() {
		assertEquals(
				"stringToBoolean value does not match expected result", false,
				Utilities.stringToBoolean(" fAlSe "));
	}

	@Test
	public void testStringToBooleanFalse3() {
		assertEquals(
				"stringToBoolean value does not match expected result", false,
				Utilities.stringToBoolean(" non boolean value"));
	}

	@Test
	public void testStringToBooleanBlank() {
		assertEquals(
				"stringToBoolean value does not match expected result", false,
				Utilities.stringToBoolean(""));
	}

	@Test
	public void testStringToBooleanBlank2() {
		assertEquals(
				"stringToBoolean value does not match expected result", false,
				Utilities.stringToBoolean(null));
	}

	@Test
	public void testMergePositions1() throws IOException {
		List<OffsetPosition> position1 = new ArrayList<OffsetPosition>();
		List<OffsetPosition> position2 = new ArrayList<OffsetPosition>();
		position1.add(new OffsetPosition(0,2));
		position2.add(new OffsetPosition(3,5));

		List<OffsetPosition> positions = Utilities.mergePositions(position1,position2);
		assertEquals(positions.size(), 2);
		assertEquals(positions.get(0).start, 0);
		assertEquals(positions.get(0).end, 2);
		assertEquals(positions.get(1).start, 3);
		assertEquals(positions.get(1).end, 5);
	}

	@Test
	public void testMergePositions2() throws IOException {
		List<OffsetPosition> position1 = new ArrayList<OffsetPosition>();
		List<OffsetPosition> position2 = new ArrayList<OffsetPosition>();
		position1.add(new OffsetPosition(0,2));
		position1.add(new OffsetPosition(4,5));
		position2.add(new OffsetPosition(3,4));
		position2.add(new OffsetPosition(8,10));

		List<OffsetPosition> positions = Utilities.mergePositions(position1,position2);
		assertEquals(positions.size(), 3);
		assertEquals(positions.get(0).start, 0);
		assertEquals(positions.get(0).end, 2);
		assertEquals(positions.get(1).start, 3);
		assertEquals(positions.get(1).end, 5);
		assertEquals(positions.get(2).start, 8);
		assertEquals(positions.get(2).end, 10);
	}

	@Test
	public void testMergePositionsOverlap() throws IOException {
		List<OffsetPosition> position1 = new ArrayList<OffsetPosition>();
		List<OffsetPosition> position2 = new ArrayList<OffsetPosition>();
		position1.add(new OffsetPosition(0,3));
		position1.add(new OffsetPosition(5,6));
		position1.add(new OffsetPosition(8,9));
		position2.add(new OffsetPosition(1,2));
		position2.add(new OffsetPosition(3,6));
		position2.add(new OffsetPosition(7,10));
		
		List<OffsetPosition> positions= Utilities.mergePositions(position1,position2);
		assertEquals(positions.size(), 2);
		assertEquals(positions.get(0).start, 0);
		assertEquals(positions.get(0).end, 6);
		assertEquals(positions.get(1).start, 7);		
		assertEquals(positions.get(1).end, 10);
	}
}
