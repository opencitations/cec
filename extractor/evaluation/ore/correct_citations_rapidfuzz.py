# CEX Evaluation Correction - Page Number Citation Matching with RapidFuzz
# 
# This code identifies citation pairs where:
# - CEX prediction has page numbers (e.g., "Gelso, 2009, pp. 254-255")
# - JATS ground truth is the same citation without page numbers (e.g., "Gelso, 2009")
# - The citation CONTEXT (full sentence text) is the SAME in both
# - The SECTION can optionally be used to validate matches
# - Creates proper matches between them in the evaluation data
#
# Requires: pip install rapidfuzz
# Usage: python correct_citations_rapidfuzz.py

import json
import re
import copy

# Try to import rapidfuzz, fall back to difflib if not available
try:
    from rapidfuzz import fuzz
    USE_RAPIDFUZZ = True
    print("Using RapidFuzz for similarity matching")
except ImportError:
    from difflib import SequenceMatcher
    USE_RAPIDFUZZ = False
    print("RapidFuzz not available, using SequenceMatcher (slower)")
    print("To use RapidFuzz: pip install rapidfuzz")


def similar_values(citation1, citation2, threshold=85):
    """
    Check if two citation contexts/section titles are similar enough to be considered the same citation.
    Uses RapidFuzz token_sort_ratio for robust matching.
    
    Args:
        citation1: First citation context text
        citation2: Second citation context text
        threshold: Similarity threshold (0-100). Default 85 = 85% similar
    
    Returns:
        Boolean indicating if citations are similar enough to be a match
    """
    # Normalize: remove extra whitespace
    c1 = ' '.join(citation1.split())
    c2 = ' '.join(citation2.split())
    
    if USE_RAPIDFUZZ:
        # Use RapidFuzz token_sort_ratio (handles word order variations)
        similarity = fuzz.token_sort_ratio(c1, c2)
    else:
        # Fall back to SequenceMatcher if RapidFuzz not available
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, c1.lower(), c2.lower()).ratio() * 100
    
    return similarity >= threshold


def reference_match_after_page_removal(pred_ref, gt_ref):
    """
    Check if prediction reference matches GT reference after removing page numbers.
    
    Args:
        pred_ref: Prediction reference (may contain page numbers)
        gt_ref: Ground truth reference
    
    Returns:
        Boolean indicating if references match after page removal
    """
    # Remove page numbers from prediction reference
    # Handles: "p. XX", "pp. XX-YY", "p. XXff", etc.
    pred_without_page = re.sub(
        r',?\s*p(?:p)?\.?\s+\d+(?:[-–]\d+)?(?:\s*f{2})?', 
        '', 
        pred_ref
    ).strip()
    
    # Check if they match
    if not pred_without_page:
        return False
    
    return (pred_without_page in gt_ref or 
            gt_ref in pred_without_page or
            (len(pred_without_page) > 10 and pred_without_page[:20] in gt_ref))


def correct_page_number_citations_with_context(input_file, output_file, 
                                               context_threshold=85,
                                               section_threshold=85,
                                               validate_section=True):
    """
    Correct page number citation mismatches in evaluation data.
    Only creates matches when BOTH reference AND citation context match.
    Optionally validates section as well.
    Uses RapidFuzz token_sort_ratio for similarity matching.
    
    Args:
        input_file: Path to original evaluation JSON
        output_file: Path to save corrected evaluation JSON
        context_threshold: Similarity threshold for citation context (0-100)
        section_threshold: Similarity threshold for section (0-100)
        validate_section: If True, also checks section similarity for complete match
    
    Returns:
        Dictionary with correction statistics
    """
    
    # Load the original data
    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Create a deep copy for the corrected version
    corrected_data = copy.deepcopy(original_data)
    
    # Track statistics
    citation_pairs_matched = 0
    documents_affected = set()
    invalid_matches_rejected = 0
    
    # Process each document
    for doc_id, doc_data in corrected_data.items():
        if doc_id == 'comprehensive_summary':
            continue
        
        detailed = doc_data['detailed_results']
        unmatched_pred = detailed.get('unmatched_predictions', {})
        unmatched_gt = detailed.get('unmatched_ground_truth', {})
        matches = detailed.get('matches', {})
        
        # Track which items to remove
        pred_ids_to_remove = set()
        gt_ids_to_remove = set()
        
        # Iterate through unmatched predictions
        for pred_cit_id, pred_data in list(unmatched_pred.items()):
            pred_reference = pred_data.get('REFERENCE', '')
            pred_citation = pred_data.get('CITATION', '')
            pred_section = pred_data.get('SECTION', '')
            
            # Check if this prediction has author-year + page number pattern
            if not re.search(r'\d{4}[^a-z]*?p(?:p)?\.?\s*\d+', 
                           pred_reference, re.IGNORECASE):
                continue
            
            # Try to find a matching ground truth
            for gt_cit_id, gt_data in list(unmatched_gt.items()):
                gt_reference = gt_data.get('REFERENCE', '')
                gt_citation = gt_data.get('CITATION', '')
                gt_section = gt_data.get('SECTION', '')
                
                # Step 1: Check if references match (after page removal)
                if not reference_match_after_page_removal(pred_reference, gt_reference):
                    continue
                
                # Step 2: Check if citation contexts match using RapidFuzz token_sort_ratio
                if not similar_values(pred_citation, gt_citation,
                                        threshold=context_threshold):
                    invalid_matches_rejected += 1
                    continue
                
                # Step 3 (Optional): Check if sections match
                if validate_section:
                    if not similar_values(pred_section, gt_section,
                                          threshold=section_threshold):
                        invalid_matches_rejected += 1
                        continue
                
                # VALID MATCH: All criteria met!
                matches[pred_cit_id] = gt_cit_id
                pred_ids_to_remove.add(pred_cit_id)
                gt_ids_to_remove.add(gt_cit_id)
                citation_pairs_matched += 1
                documents_affected.add(doc_id)
                break
        
        # Remove the matched items from unmatched categories
        for pred_id in pred_ids_to_remove:
            if pred_id in unmatched_pred:
                del unmatched_pred[pred_id]
        
        for gt_id in gt_ids_to_remove:
            if gt_id in unmatched_gt:
                del unmatched_gt[gt_id]
        
        # Recalculate summary metrics for this document
        total_matches = len(matches)
        total_unmatched_pred = len(unmatched_pred)
        total_unmatched_gt = len(unmatched_gt)
        
        # Get original ground truth and predictions count (these don't change)
        original_summary = original_data[doc_id]['summary']
        total_gt = original_summary['total_ground_truth']
        total_pred = original_summary['total_predictions']
        
        # Recalculate metrics
        precision = total_matches / total_pred if total_pred > 0 else 0
        recall = total_matches / total_gt if total_gt > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Update document summary
        doc_data['summary'] = {
            'total_ground_truth': total_gt,
            'total_predictions': total_pred,
            'matches': total_matches,
            'mismatches': total_unmatched_pred,
            'unmatched_ground_truth': total_unmatched_gt,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    # Calculate overall comprehensive summary
    total_gt_corrected = sum(
        doc_data['summary']['total_ground_truth'] 
        for doc_id, doc_data in corrected_data.items() 
        if doc_id != 'comprehensive_summary'
    )
    total_pred_corrected = sum(
        doc_data['summary']['total_predictions'] 
        for doc_id, doc_data in corrected_data.items() 
        if doc_id != 'comprehensive_summary'
    )
    total_matches_corrected = sum(
        doc_data['summary']['matches'] 
        for doc_id, doc_data in corrected_data.items() 
        if doc_id != 'comprehensive_summary'
    )
    total_mismatches_corrected = total_pred_corrected - total_matches_corrected
    
    precision_corrected = total_matches_corrected / total_pred_corrected if total_pred_corrected > 0 else 0
    recall_corrected = total_matches_corrected / total_gt_corrected if total_gt_corrected > 0 else 0
    f1_corrected = 2 * (precision_corrected * recall_corrected) / (precision_corrected + recall_corrected) if (precision_corrected + recall_corrected) > 0 else 0
    
    # Add comprehensive summary
    validation_note = f"context={context_threshold}"
    if validate_section:
        validation_note += f", section={section_threshold}"
    
    corrected_data['comprehensive_summary'] = {
        'total_ground_truth': total_gt_corrected,
        'total_predictions': total_pred_corrected,
        'matches': total_matches_corrected,
        'mismatches': total_mismatches_corrected,
        'precision': precision_corrected,
        'recall': recall_corrected,
        'f1_score': f1_corrected,
        'note': f'Corrected dataset: citation pairs with context-validated page number matching (RapidFuzz token_sort_ratio, {validation_note})'
    }
    
    # Save the corrected dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(corrected_data, f, indent=2)
    
    # Prepare return statistics
    original_summary = original_data['comprehensive_summary']
    stats = {
        'citation_pairs_matched': citation_pairs_matched,
        'invalid_matches_rejected': invalid_matches_rejected,
        'documents_affected': len(documents_affected),
        'context_threshold': context_threshold,
        'section_threshold': section_threshold,
        'validate_section': validate_section,
        'original_metrics': {
            'matches': original_summary['matches'],
            'precision': original_summary['precision'],
            'recall': original_summary['recall'],
            'f1_score': original_summary['f1_score']
        },
        'corrected_metrics': {
            'matches': total_matches_corrected,
            'precision': precision_corrected,
            'recall': recall_corrected,
            'f1_score': f1_corrected
        },
        'improvements': {
            'matches': total_matches_corrected - original_summary['matches'],
            'precision': precision_corrected - original_summary['precision'],
            'recall': recall_corrected - original_summary['recall'],
            'f1_score': f1_corrected - original_summary['f1_score']
        }
    }
    
    return stats


def print_correction_report(stats):
    """Print a formatted report of the corrections."""
    
    print("="*100)
    print("CEX EVALUATION CORRECTION REPORT")
    print("(WITH RAPIDFUZZ TOKEN_SORT_RATIO CONTEXT VALIDATION)")
    print("="*100)
    print()
    
    print(f"Context Threshold: {stats['context_threshold']}")
    print(f"Section Validation: {stats['validate_section']}")
    if stats['validate_section']:
        print(f"Section Threshold: {stats['section_threshold']}")
    print(f"Citation pairs matched: {stats['citation_pairs_matched']}")
    print(f"Invalid matches rejected: {stats['invalid_matches_rejected']}")
    print(f"Documents affected: {stats['documents_affected']}")
    print()
    
    print("METRICS COMPARISON:")
    print("-"*100)
    print(f"{'Metric':<25} {'Original':<20} {'Corrected':<20} {'Change':<20}")
    print("-"*100)
    
    orig = stats['original_metrics']
    corr = stats['corrected_metrics']
    impr = stats['improvements']
    
    print(f"{'Matches':<25} {orig['matches']:<20,} {corr['matches']:<20,} {impr['matches']:+,}")
    print(f"{'Precision':<25} {orig['precision']:<20.6f} {corr['precision']:<20.6f} {impr['precision']:+.6f}")
    print(f"{'Recall':<25} {orig['recall']:<20.6f} {corr['recall']:<20.6f} {impr['recall']:+.6f}")
    print(f"{'F1-Score':<25} {orig['f1_score']:<20.6f} {corr['f1_score']:<20.6f} {impr['f1_score']:+.6f}")



