
import tempfile
import unittest
from pathlib import Path

from lxml import etree


from create_corpus import transform_jats_to_tei


class TestJatsTei(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Persistent directory for the whole test class
        cls.tmpdir = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmpdir.name)

        cls.xml_file = tmp / "input.xml"
        cls.out_file = tmp / "output.xml"

        cls.saxon_path = "/home/marta/saxon/SaxonHE12-8J/saxon-he-12.8.jar"
        cls.xslt_file = "/home/marta/cec/extractor/evaluation/ore/jats-to-tei.xsl"

    @classmethod
    def tearDownClass(cls):
        # Clean up after all tests are done
        cls.tmpdir.cleanup()


    def test_footnotes_1(self):

        input_xml = """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
        <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                 xmlns:xlink="http://www.w3.org/1999/xlink"
                 article-type="research-article"
                 dtd-version="1.2"
                 xml:lang="en">
        <back>
            <fn-group>
            <fn id="FN1">
                <p>
                    <sup>1</sup>Overall, the the dataset has been cited 1439 times according to a Google Scholar query on 26 August 2023.</p>
            </fn>
        </fn-group>
        </back>
        </article>
        """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <note>
        notes = root.findall(".//tei:note", namespaces=ns)
        self.assertEqual(len(notes), 1, "No <note> elements found in TEI output")

        for note in notes:
            note_id = note.get("{http://www.w3.org/XML/1998/namespace}id")
            self.assertIsNotNone(note_id, "<note> missing xml:id")

            has_p = note.find(".//tei:p", namespaces=ns) is not None
            assert has_p, f"<note xml:id='{note.get('{http://www.w3.org/XML/1998/namespace}id')}' has no <p>"

            # 4. Print for debugging
            print(f"Test {self._testMethodName}",etree.tostring(note, encoding="unicode"))

    def test_footnotes_2(self):

        input_xml = """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
        <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                 xmlns:xlink="http://www.w3.org/1999/xlink"
                 article-type="research-article"
                 dtd-version="1.2"
                 xml:lang="en">
        <back>
            <fn-group>
                <fn id="FN1">
                    <p>
                        <sup>1</sup>Overall, the the dataset has been cited 1439 times according to a Google Scholar query on 26 August 2023.</p>
                </fn>
                <fn id="FN2">
                    <p>
                        <sup>2</sup>Overall, the the dataset has been cited 1439 times according to a Google Scholar query on 26 August 2023.</p>
                    <p>Overall, the the dataset has been cited 1439 times according to a Google Scholar query on 26 August 2023.</p>
                </fn>
            </fn-group>
        </back>
        </article>
        """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}


        # 3. Find <note>
        notes = root.findall(".//tei:note", namespaces=ns)
        self.assertEqual(len(notes), 2, "No <note> elements found in TEI output")

        for note in notes:
            note_id = note.get("{http://www.w3.org/XML/1998/namespace}id")
            self.assertIsNotNone(note_id, "<note> missing xml:id")

            has_p = note.find(".//tei:p", namespaces=ns) is not None
            assert has_p, f"<note xml:id='{note.get('{http://www.w3.org/XML/1998/namespace}id')}' has no <p>"

            # 4. Print for debugging
            print(f"Test {self._testMethodName}", etree.tostring(note, encoding="unicode"))

    def test_footnotes_3(self):
        input_xml = """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
        <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                 xmlns:xlink="http://www.w3.org/1999/xlink"
                 article-type="research-article"
                 dtd-version="1.2"
                 xml:lang="en">
        <back>
        <fn-group>
            <fn>
                <p id="FN1">
                    <sup>1</sup>
                    <ext-link ext-link-type="uri"
                         xlink:href="https://www.isi.fraunhofer.de/de/competence-center/energiepolitik-energiemaerkte/projekte/dia-core_330663.html">https://www.isi.fraunhofer.de/de/competence-center/energiepolitik-energiemaerkte/projekte/dia-core_330663.html</ext-link>
                </p>
                <p id="FN2">
                    <sup>2</sup>
                    <ext-link ext-link-type="uri" xlink:href="http://re-frame.eu/">http://re-frame.eu/</ext-link>
                </p>
                <p id="FN3">
                    <sup>3</sup>Nevertheless, in case of interest to obtain more information than the dataset in the extended data (
                    <xref ref-type="bibr" rid="ref-1">Br&#x00fc;ckmann 
                        <italic toggle="yes">et al.</italic>, 2021</xref>) or a more detailed sub-set, the readers are advised to contact the main data collection coordinator Mo&#x00ef;ra Jimeno under the following e-mail address: 
                    <ext-link ext-link-type="uri" xlink:href="mailto:mj@eclareon.com">mj@eclareon.com</ext-link>.</p>
            </fn>
        </fn-group>
        </back>
        </article>
        """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <note>
        notes = root.findall(".//tei:note", namespaces=ns)
        self.assertEqual(len(notes), 3, f"{len(notes)} <note> elements found in TEI output")

        for note in notes:
            note_id = note.get("{http://www.w3.org/XML/1998/namespace}id")
            self.assertIsNotNone(note_id, "<note> missing xml:id")

            has_p = note.find(".//tei:p", namespaces=ns) is not None
            assert has_p, f"<note xml:id='{note.get('{http://www.w3.org/XML/1998/namespace}id')}' has no <p>"

            print(f"Test {self._testMethodName}", etree.tostring(note, encoding="unicode"))


    def test_footnotes_4(self):
        input_xml = """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
        <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                 xmlns:xlink="http://www.w3.org/1999/xlink"
                 article-type="research-article"
                 dtd-version="1.2"
                 xml:lang="en">
        <back>
        <fn-group>
            <fn>
                <p id="FN1">
                    <sup>1</sup> The current French national strategy is driven by the 4
                    <sup>th</sup> French national radon action plan (2020&#x2013;2024) and, when it comes to radon in houses, actions are concentrated on information and awareness The single regulatory requirement consists in an obligation to inform the buyers/tenants of real estate located in radon prone areas prior to a property transaction (article L. 125-5 of the French Environment Code). The radon prone areas are listed by the 27 June 2018 Regulatory Order.</p>
            </fn>
            <fn>
                <p id="FN2">
                    <sup>2</sup> The local health contract (CLS) is a contractual document established between a local public administration (generally a group of communities) and the Regional Health Agency (ARS) which describe a local strategy intended for the improvement of the health of the population and include different objectives aligned with the local context (
                    <italic toggle="yes">e.g</italic>. allergy, access to health care, &#x2026;) and the means to achieve them. Experiences show that some administration can consider including an item about the measurement and the management of radon in houses within the CLS.</p>
            </fn>
        </fn-group>
        </back>
        </article>
        """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <note>
        notes = root.findall(".//tei:note", namespaces=ns)
        self.assertEqual(len(notes), 2, f"{len(notes)} <note> elements found in TEI output")

        for note in notes:
            note_id = note.get("{http://www.w3.org/XML/1998/namespace}id")
            self.assertIsNotNone(note_id, "<note> missing xml:id")

            has_p = note.find(".//tei:p", namespaces=ns) is not None
            assert has_p, f"<note xml:id='{note.get('{http://www.w3.org/XML/1998/namespace}id')}' has no <p>"

            print(f"Test {self._testMethodName}", etree.tostring(note, encoding="unicode"))


    def test_footnotes_5(self):
        input_xml = """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
        <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                 xmlns:xlink="http://www.w3.org/1999/xlink"
                 article-type="research-article"
                 dtd-version="1.2"
                 xml:lang="en">
                <back>
                    <fn-group>
                        <fn>
                            <p id="FN1">
                                <sup>1</sup> See 
                                <ext-link ext-link-type="uri"
                                     xlink:href="https://scholar.google.com/intl/de/scholar/inclusion.html#content">https://scholar.google.com/intl/de/scholar/inclusion.html#content</ext-link>
                            </p>
                        </fn>
                        <fn>
                            <p id="FN2">
                                <sup>2</sup> ThatCamp stands for &#x201c;The Humanities And Technology Camp&#x201d;. It is a so-called unconference based on the BarCamp concept: an open, agile and spontaneous meeting where participants learn and work together by engaging in group discussions, co-working sessions or other forms of collaborative work. People engage with each other to &#x201c;create, build, write, hack, and solve problems&#x201d; (
                                <ext-link ext-link-type="uri" xlink:href="https://thatcamp.org/about/index.html">https://thatcamp.org/about/index.html</ext-link>).</p>
                        </fn>
                        <fn>
                            <p id="FN3">
                                <sup>3</sup> The eight sessions were dedicated to the following topics (suggested by participants, and voted by them):  1) How to disseminate and make Digital Scholarship discoverable:experiences, ideas and proposals in order to have new forms of scholarship, based on electronic publishing, more discoverable in the infosphere</p>
                            <p>2) Difficulties in Discovery: What are your annoyances? Vent them here</p>
                            <p>3) What are the obstacles and challenges in offering a discovery service and do they apply to Open Access resources?</p>
                            <p>4) Overcoming the discoverability crisis</p>
                            <p>5) Ideas to improve peer reviews in Scientific documents</p>
                            <p>6) What is the meaning of &#x201c;discovery&#x201d; in the different languages?</p>
                            <p>7) If you had a complete discovery portal for SSH research outcomes, how would you like to use it? What functionality would you like to find?</p>
                            <p>8) What do I have to keep in mind as a researcher when it comes to thinking of discovery systems? Optimizing keywords, just this?</p>
                        </fn>
                        <fn>
                            <p id="FN4">
                                <sup>4</sup> https://www.operas-eu.org/</p>
                        </fn>
                    </fn-group>
                </back>
        </article>"""

        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <note>
        notes = root.findall(".//tei:note", namespaces=ns)
        self.assertEqual(len(notes), 4, f"{len(notes)} <note> elements found in TEI output")

        for note in notes:
            note_id = note.get("{http://www.w3.org/XML/1998/namespace}id")
            self.assertIsNotNone(note_id, "<note> missing xml:id")

            has_p = note.find(".//tei:p", namespaces=ns) is not None
            assert has_p, f"<note xml:id='{note.get('{http://www.w3.org/XML/1998/namespace}id')}' has no <p>"

            print(f"Test {self._testMethodName}", etree.tostring(note, encoding="unicode"))


    def test_footnote_6(self):
        input_xml = """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
                <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                         xmlns:xlink="http://www.w3.org/1999/xlink"
                         article-type="research-article"
                         dtd-version="1.2"
                         xml:lang="en">
                <back>
                    <fn-group>
                        <fn>
                            <p id="FN1">
                                <sup>1</sup>Overall, the the dataset has been cited 1439 times according to a Google Scholar query on 26 August 2023.</p>
                        </fn>
                        <fn>
                            <p id="FN2">
                                <sup>2</sup>Overall, the the dataset has been cited 1439 times according to a Google Scholar query on 26 August 2023.</p>
                            <p>Overall, the the dataset has been cited 1439 times according to a Google Scholar query on 26 August 2023.</p>
                        </fn>
                    </fn-group>
                </back>
                </article>
                """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <note>
        notes = root.findall(".//tei:note", namespaces=ns)
        self.assertEqual(len(notes), 2, "No <note> elements found in TEI output")

        for note in notes:
            note_id = note.get("{http://www.w3.org/XML/1998/namespace}id")
            self.assertIsNotNone(note_id, "<note> missing xml:id")

            has_p = note.find(".//tei:p", namespaces=ns) is not None
            assert has_p, f"<note xml:id='{note.get('{http://www.w3.org/XML/1998/namespace}id')}' has no <p>"

            # 4. Print for debugging
            print(f"Test {self._testMethodName}", etree.tostring(note, encoding="unicode"))

    def test_n_sec_title(self):
        input_xml="""<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
                <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                         xmlns:xlink="http://www.w3.org/1999/xlink"
                         article-type="review-article"
                         dtd-version="1.2"
                         xml:lang="en">
                <body>
                <sec>
                <title>2. The dark matter test science project</title>
                <p id="S2">Through making use of ESCAPE tools and services hosted on the EOSC, the Dark Matter TSP seeks to store, distribute, and provide FAIR software and data access for dark matter research in order to highlight synergies between different research communities and allow them to collaborate to produce new results
                    <sup>
                        <xref ref-type="bibr" rid="ref-53">53</xref>
                    </sup>.
                </p>
                </sec>
                <sec>
                <title>2.1 The ATLAS particle detector</title>
                <p id="S2">Through making use of ESCAPE tools and services hosted on the EOSC, the Dark Matter TSP seeks to store, distribute, and provide FAIR software and data access for dark matter research in order to highlight synergies between different research communities and allow them to collaborate to produce new results
                    <sup>
                        <xref ref-type="bibr" rid="ref-53">53</xref>
                    </sup>.
                </p>
                </sec>
                <sec>
                <title>Translating to astrophysical constraints</title>
                <p id="S2">Through making use of ESCAPE tools and services hosted on the EOSC, the Dark Matter TSP seeks to store, distribute, and provide FAIR software and data access for dark matter research in order to highlight synergies between different research communities and allow them to collaborate to produce new results
                    <sup>
                        <xref ref-type="bibr" rid="ref-53">53</xref>
                    </sup>.
                </p>
                </sec>
                </body>
                </article>
                """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <head>
        heads = root.findall(".//tei:head", namespaces=ns)
        head0= heads[0]
        head1 = heads[1]
        head2 = heads[2]
        n_attribute0 = head0.get("n")
        n_attribute1 = head1.get("n")
        n_attribute2 = head2.get("n")
        self.assertEqual(n_attribute0, "2.")
        self.assertEqual(n_attribute1, "2.1")
        self.assertEqual(n_attribute2, None)
        self.assertEqual(head0.text, "The dark matter test science project")
        self.assertEqual(head1.text, "The ATLAS particle detector")
        self.assertEqual(head2.text, "Translating to astrophysical constraints")

    def test_data_availability(self):
        input_xml="""<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
                <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                         xmlns:xlink="http://www.w3.org/1999/xlink"
                         article-type="review-article"
                         dtd-version="1.2"
                         xml:lang="en">
                <body>
                <sec>
                <title>2. The dark matter test science project</title>
                <p id="S2">Through making use of ESCAPE tools and services hosted on the EOSC, the Dark Matter TSP seeks to store, distribute, and provide FAIR software and data access for dark matter research in order to highlight synergies between different research communities and allow them to collaborate to produce new results
                    <sup>
                        <xref ref-type="bibr" rid="ref-53">53</xref>
                    </sup>.
                </p>
                </sec>
                </body>
                <back>
                <sec sec-type="data-availability">
                    <title>Data availability</title>
                    <p>This study uses data from 14 national and regional case studies as reported by 
                        <xref ref-type="bibr" rid="ref-35">Maring 
                            <italic toggle="yes">et al.</italic> (2025)</xref>. The source materials underlying the results are openly available from: 
                        <ext-link ext-link-type="uri" xlink:href="http://hdl.handle.net/10138/596051">http://hdl.handle.net/10138/596051</ext-link>.</p>
                </sec>
                </back>
                </article>
                """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <head>

        heads = root.findall(".//tei:head", namespaces=ns)
        head0= heads[0]
        head1 = heads[1]
        div1 = root.findall(".//tei:div", namespaces=ns)[1]

        n_attribute0 = head0.get("n")
        attribute1 = div1.get("type")

        self.assertEqual(n_attribute0, "2.")
        self.assertEqual(attribute1,"availability")
        self.assertEqual(head0.text, "The dark matter test science project")
        self.assertEqual(head1.text, "Data availability")

    def test_acknowledgement(self):
        input_xml="""<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20190208//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
                <article xmlns:mml="http://www.w3.org/1998/Math/MathML"
                         xmlns:xlink="http://www.w3.org/1999/xlink"
                         article-type="review-article"
                         dtd-version="1.2"
                         xml:lang="en">
                <body>
                <sec>
                <title>2. The dark matter test science project</title>
                <p id="S2">Through making use of ESCAPE tools and services hosted on the EOSC, the Dark Matter TSP seeks to store, distribute, and provide FAIR software and data access for dark matter research in order to highlight synergies between different research communities and allow them to collaborate to produce new results
                    <sup>
                        <xref ref-type="bibr" rid="ref-53">53</xref>
                    </sup>.
                </p>
                </sec>
                </body>
                <back>
                <ack>
                    <title>Acknowledgements</title>
                    <p>J.M. and T.S. acknowledge computational resources provided by the Vienna Scientific Cluster. We are deeply indebted to the many authors that contribute to the vibrant scientific Python ecosystem.</p>
                </ack>
                </back>
                </article>
                """
        self.xml_file.write_text(input_xml)

        transform_jats_to_tei(
            str(self.xml_file),
            str(self.out_file),
            saxon_path=self.saxon_path,
            xslt_path=str(self.xslt_file)
        )

        tree = etree.parse(self.out_file)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # 3. Find <head>

        heads = root.findall(".//tei:head", namespaces=ns)
        head0= heads[0]
        head1 = heads[1]
        div1 = root.findall(".//tei:div", namespaces=ns)[1]

        n_attribute0 = head0.get("n")
        attribute1 = div1.get("type")
        p_in_div = root.findall(".//tei:div/tei:p", namespaces=ns)[1]

        self.assertEqual(n_attribute0, "2.")
        self.assertEqual(attribute1,"acknowledgement")
        self.assertEqual(head0.text, "The dark matter test science project")
        self.assertEqual(head1.text, "Acknowledgements")
        self.assertEqual(p_in_div.text, "J.M. and T.S. acknowledge computational resources provided by the Vienna Scientific Cluster. We are deeply indebted to the many authors that contribute to the vibrant scientific Python ecosystem.")



