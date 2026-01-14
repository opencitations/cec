"""
Unified Citation Extraction Pipeline Orchestrator

Orchestrates the complete workflow:
1. download_xml.py      → Download JATS XML files from ORE
2. create_corpus.py     → Process XML, download PDFs, transform to TEI
3. create_predictions.py → Send PDFs to CEX API, get predictions
4. correct_citations_rapidfuzz.py → Correct page number mismatches using RapidFuzz

Usage:
    python pipeline_unified.py --all                    # Run all steps
    python pipeline_unified.py --step download          # Run only download
    python pipeline_unified.py --step corpus            # Run only corpus creation
    python pipeline_unified.py --step predictions       # Run only predictions
    python pipeline_unified.py --step corrections       # Run only corrections
    python pipeline_unified.py --step corpus --step predictions  # Run multiple steps
"""
import asyncio
import os.path
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {

    'dirs': {
        'log_dir': '/home/marta/Scrivania/ORE_PROVA',
        'xml_download': '/home/marta/Scrivania/ORE_PROVA/xml',
        'corpus': '/home/marta/Scrivania/ORE_PROVA/ore_corpus',
        'predictions': '/home/marta/Scrivania/ORE_PROVA/predictions',
        'cex_zips': '/home/marta/Scrivania/ORE_PROVA/out_CEX_zips',
    },
    'files': {
        'listing_url': 'https://open-research-europe.ec.europa.eu/published-xml-urls',
        'saxon_jar': '/home/marta/saxon/SaxonHE12-8J/saxon-he-12.8.jar',
        'xslt': 'jats-to-tei.xsl',
        'evaluation_input': '/media/marta/T7 Touch/CEX_evaluation_article/ORE/partial70_section.json',
        'evaluation_output': '/media/marta/T7 Touch/CEX_evaluation_article/ORE/partial70_section_correct_pages.json'
    },
    'cex_api': {
        'url': 'http://test.opencitations.net:81/cex/api/extractor',
        'timeout': 480,  # 8 minutes per PDF
    },
    'matching': {
        'context_threshold': 70,
        'section_threshold': 70,
        'validate_section': True,
    },
    'download_concurrency': 10
}


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_file: str = None) -> logging.Logger:
    """Configure logging to file and console."""
    if log_file is None:
        log_dir = CONFIG['dirs']['log_dir']
        log_file = os.path.join(log_dir, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logger = logging.getLogger('Pipeline')
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = setup_logging()


# ============================================================================
# STEP 1: DOWNLOAD XML
# ============================================================================

def step_download_xml():
    """Download JATS XML files from Open Research Europe."""
    logger.info("=" * 80)
    logger.info("STEP 1: DOWNLOADING XML FILES FROM ORE")
    logger.info("=" * 80)

    xml_dir = CONFIG['dirs']['xml_download']
    concurrency = CONFIG['download_concurrency']
    listing_url = CONFIG['files']['listing_url']

    try:
        Path(xml_dir).mkdir(parents=True, exist_ok=True)

        # Import and run download_xml
        from download_xml import main as download_main
        # Run async download
        asyncio.run(download_main(concurrency, listing_url, xml_dir))

        xml_files = list(Path(xml_dir).glob("*.xml"))
        if len(xml_files) > 0:
            logger.info(f"✅ XML download completed successfully ({len(xml_files)} files)")
            return True
        else:
            logger.error("❌ No files were downloaded")
            return False

    except Exception as e:
        logger.error(f"❌ Error during XML download: {e}", exc_info=True)
        return False


# ============================================================================
# STEP 2: CREATE CORPUS
# ============================================================================

def step_create_corpus():
    """Process JATS XML, download PDFs, transform to TEI."""
    logger.info("=" * 80)
    logger.info("STEP 2: CREATING CORPUS (PDF download + JATS→TEI transformation)")
    logger.info("=" * 80)

    try:
        from create_corpus import (
            get_latest_xml_versions,
            download_pdf_from_xml,
            transform_jats_to_tei,
            fix_multi_references,
            fix_whitespaces_empty_tags
        )

        xml_dir = CONFIG['dirs']['xml_download']
        corpus_dir = CONFIG['dirs']['corpus']
        saxon_jar = CONFIG['files']['saxon_jar']
        xslt_file = CONFIG['files']['xslt']

        Path(corpus_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Looking for XML files in: {xml_dir}")
        latest_xml_files = get_latest_xml_versions(xml_dir)
        logger.info(f"Found {len(latest_xml_files)} XML files to process")

        success_count = 0
        error_count = 0

        for xml_file in latest_xml_files:
            try:
                logger.info(f"Processing: {xml_file.name}")
                download_pdf_from_xml(xml_file, corpus_dir, saxon_jar, xslt_file)
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Error processing {xml_file}: {e}", exc_info=True)
                error_count += 1

        logger.info(f"Corpus creation completed: {success_count} succeeded, {error_count} failed")
        return error_count == 0

    except Exception as e:
        logger.error(f"❌ Error during corpus creation: {e}", exc_info=True)
        return False


# ============================================================================
# STEP 3: CREATE PREDICTIONS
# ============================================================================

def step_create_predictions():
    """Send PDFs to CEX API and collect predictions."""
    logger.info("=" * 80)
    logger.info("STEP 3: CREATING PREDICTIONS (CEX API)")
    logger.info("=" * 80)

    try:
        from create_predictions import (
            process_pdf,
            run_with_timeout_process,
            log as log_predictions
        )

        pdf_to_process = Path(CONFIG['dirs']['corpus']).rglob('*.pdf')
        output_predictions = CONFIG['dirs']['predictions']
        output_zips = CONFIG['dirs']['cex_zips']
        timeout = CONFIG['cex_api']['timeout']


        Path(output_predictions).mkdir(parents=True, exist_ok=True)
        Path(output_zips).mkdir(parents=True, exist_ok=True)

        logger.info(f"Predictions output: {output_predictions}")

        pdf_files = list(pdf_to_process)
        logger.info(f"Found {len(pdf_files)} PDFs to process")

        success_count = 0
        failed_count = 0

        for pdf in pdf_files:
            zip_name = pdf.stem + '.zip'
            json_name = pdf.stem + '.json'
            zip_path = Path(output_zips) / zip_name
            json_path = Path(output_predictions) / json_name

            if zip_path.exists() and json_path.exists():
                logger.info(f"⏩ Skipping {pdf.name}: already processed")
                continue

            logger.info(f"Processing: {pdf.name}")
            success, error = run_with_timeout_process(
                process_pdf,
                args=(str(pdf), str(zip_path), str(json_path)),
                timeout=timeout
            )

            if success:
                success_count += 1
            else:
                logger.error(f"❌ Failed to process {pdf.name}: {error}")
                failed_count += 1

        logger.info(f"Predictions completed: {success_count} succeeded, {failed_count} failed")
        return failed_count == 0

    except Exception as e:
        logger.error(f"❌ Error during predictions: {e}", exc_info=True)
        return False


# ============================================================================
# PIPELINE ORCHESTRATION
# ============================================================================

def run_pipeline(steps):
    """Run the specified pipeline steps."""
    logger.info("\n" + "=" * 80)
    logger.info("CITATION EXTRACTION PIPELINE STARTED")
    logger.info(f"Steps to execute: {', '.join(steps)}")
    logger.info("=" * 80 + "\n")

    step_functions = {
        'download': step_download_xml,
        'corpus': step_create_corpus,
        'predictions': step_create_predictions
    }

    results = {}

    for step in steps:
        if step not in step_functions:
            logger.error(f"❌ Unknown step: {step}")
            continue

        try:
            logger.info(f"\n▶️  Starting step: {step}")
            success = step_functions[step]()
            results[step] = 'SUCCESS' if success else 'FAILED'

            if success:
                logger.info(f"✅ Step '{step}' completed successfully\n")
            else:
                logger.warning(f"⚠️  Step '{step}' completed with errors\n")

        except Exception as e:
            logger.error(f"💥 Step '{step}' crashed: {e}", exc_info=True)
            results[step] = 'CRASHED'

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 80)

    for step, status in results.items():
        symbol = "✅" if status == "SUCCESS" else "❌" if status == "FAILED" else "💥"
        logger.info(f"{symbol} {step:15s} → {status}")

    logger.info("=" * 80 + "\n")

    all_successful = all(s == "SUCCESS" for s in results.values())
    return all_successful


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Parse arguments and run pipeline."""
    parser = argparse.ArgumentParser(
        description="Citation Extraction Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run all steps:
    python pipeline_unified.py --all

  Run specific steps:
    python pipeline_unified.py --step download --step corpus

  Run only predictions:
    python pipeline_unified.py --step predictions
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true',
                       help='Run all pipeline steps in order')
    group.add_argument('--step', action='append', dest='steps',
                       choices=['download', 'corpus', 'predictions'],
                       help='Specific step to run (can be used multiple times)')

    parser.add_argument('--log', type=str, default=None,
                        help='Log file path (default: auto-generated)')

    args = parser.parse_args()

    if args.all:
        steps = ['download', 'corpus', 'predictions']
    else:
        steps = args.steps

    success = run_pipeline(steps)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()