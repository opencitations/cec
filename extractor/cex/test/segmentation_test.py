import os
import unittest
from pathlib import Path
from lxml import etree

from extractor.cex.combined import TEIXMLtoJSONConverter

ROOT_DIR = Path(__file__).resolve().parent.parent  # Adjust based on your project structure
BASE = os.path.join(ROOT_DIR, "test", "segmentation")
INPUT_DIR = os.path.join(ROOT_DIR, "input")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")



class TestSegmentation(unittest.TestCase):
    input_file = os.path.join(INPUT_DIR, "ENE_EV12.grobid.tei.xml")
    output_json = os.path.join(OUTPUT_DIR, "ENE_EV12.json")
    auxiliar_file = os.path.join(BASE, 'special_cases.json')

    @classmethod
    def setUpClass(cls):
        cls.json_converter = TEIXMLtoJSONConverter(cls.input_file, cls.output_json, cls.auxiliar_file, False)

    def test_find_sentences(self):
        div = """<div xmlns="http://www.tei-c.org/ns/1.0"><head n="1.1.">CCHP system</head><p>Combined cooling, heating and power (CCHP) system is named directly from energy demand types, it is an efficient method to provide two kinds of thermal energy and electricity simultaneously. An energy flow structure in a specific CCHP system is illustrated in Fig. <ref type="figure" coords="1,252,68,565,90,3,38,7,17" target="#fig_0">1</ref>. The top lines represent energy sources, the rectangular boxes represent energy conversion technologies, the circular boxes represent energy demands (electricity demand, cooling demand and heating demand) and bottom lines represent energy storage systems. These four elements form a sustainable energy system and can be enriched by utilizing renewable energy, adopting various conversion technologies and expanding functions. In conventional CCHP systems, prime mover (PM) such as gas turbine (GT) converts primary energy into electricity. The waste heat otherwise discharged is recovered for space heating and cooling demands through absorption cooling (ABC) or absorption heating (ABH). Auxiliary components such as electric chiller (EC), heat pump (EH) or boiler are added to the system to fulfill extra cooling and heating demands when necessary. Overall, a CCHP system can achieve over 80% overall energy efficiency for different primary energy inputs, which is much higher than separated generation systems <ref type="bibr" coords="1,519,98,555,41,10,11,7,17" target="#b0">[1]</ref>. CCHP system capacity ranges from below 20 kW to above 10 MW. And it has proliferated in residential applications from commercial applications due to expansion of small-scale power generation units (PGU) such as microturbine (MT), Stirling engine (SE) and fuel cell (FC).</p><p>There are three steps for a CCHP system to be implemented successfully: components modeling, system planning and system control <ref type="bibr" coords="1,306,60,628,65,10,10,7,17" target="#b1">[2]</ref>. Accurate mathematical modeling provides detailed characteristics of every components and energy flow, and sets the basis for the next two stages. During the planning stage, energy conversion technologies https://doi.org/10.1016/j.rser.2019.109344 Received 3 January 2019; Received in revised form 15 August 2019; Accepted 15 August 2019 and subsystems' capacities are decided. In the last stage, the system control strategies are designed and implemented. No matter in which stages of implementing a CCHP system, decision makers are always seeking for higher energy efficiency, lower economic cost, and lower environmental impact (3E). Therefore, optimization is a topic that cannot be ignored.</p></div>"""
        root = etree.fromstring(div)
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        refs = root.findall(".//tei:p/tei:ref[@type='bibr']", namespaces=ns)
        for ref in refs:
            text_bef_ref = self.json_converter.get_text_before_ref(ref,ns)
            print(text_bef_ref)
