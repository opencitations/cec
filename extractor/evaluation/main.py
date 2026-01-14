import argparse
import re
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from rapidfuzz import fuzz

# Constants and thresholds
SIMILARITY_THRESHOLD = 70
ADDITIONAL_KEY_SIM_THRESHOLD = 70


# Improved normalization: preserve whitespaces and word separation,
# lowercase and remove limited punctuation inside words but keep spaces.
def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    # Normalize unicode
    text = text.lower()

    # Remove select punctuation but preserve spaces and word separation
    # We'll keep basic word separators like spaces, hyphens, and apostrophes (optional)
    text = re.sub(r'[“”‘’"(),:;{}\[\]<>«»‹›]', '', text)

    # Normalize multiple spaces to single spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def normalize_citation_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    normalized = entry.copy()
    normalized["SECTION"] = normalize_text(entry.get("SECTION", ""))
    normalized["CITATION"] = normalize_text(entry.get("CITATION", ""))
    normalized["REFERENCE"] = normalize_text(entry.get("REFERENCE", ""))
    return normalized


def load_and_normalize_json(filepath: str) -> Tuple[Dict[Any, Dict[str, Any]], Dict[Any, Dict[str, Any]]]:
    """Load JSON and return both normalized (for matching) and original (for reports)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data_orig = json.load(f)

    data_norm = {k: normalize_citation_entry(v) for k, v in data_orig.items()}
    return data_norm, data_orig  # normalized, original


def build_signature(entry: Dict[str, Any], keys=("REFERENCE", "CITATION")) -> str:
    """Create a composite signature to index entries by relevant keys."""
    parts = [entry.get(k, "") for k in keys]
    return "||".join(parts)


def index_ground_truth(gt_pre: Dict[str, Dict[str, Any]], keys=("REFERENCE", "CITATION")) -> Dict[str, list]:
    sig_index = {}
    for k, entry in gt_pre.items():
        sig = build_signature(entry, keys=keys)
        sig_index.setdefault(sig, []).append(k)
    return sig_index


def fuzzy_similar(a: str, b: str) -> int:
    """Fuzzy similarity using rapidfuzz on normalized strings."""
    if not a or not b:
        return 0
    return fuzz.token_sort_ratio(a, b)


def is_similar(entry1: Dict[str, Any], entry2: Dict[str, Any], keys: tuple) -> bool:
    """Check if all keys meet the similarity threshold."""
    for key in keys:
        if fuzzy_similar(entry1.get(key, ""), entry2.get(key, "")) <= SIMILARITY_THRESHOLD:
            return False
    return True

def evaluate_file(
        pred_path: str,
        gt_path: str,
        partial: bool = True,
        additional_keys: Optional[list] = None
) -> Tuple[str, Dict[str, Any]]:
    """Evaluate using normalized data for matching, original data for reports."""
    pred_norm, pred_orig = load_and_normalize_json(pred_path)
    gt_norm, gt_orig = load_and_normalize_json(gt_path)

    total_gt = len(gt_norm)
    total_pred = len(pred_norm)
    gt_index = index_ground_truth(gt_norm)
    matched_gt = set()
    matches = {}
    partial_matches = {}
    unmatched_preds = {}
    gt_keys_all = set(gt_orig.keys())

    for pred_k, pred_entry_norm in pred_norm.items():
        sig = build_signature(pred_entry_norm)
        candidates = gt_index.get(sig, [])
        found = None
        fully_matched = False

        # Try signature candidates first
        for cand in candidates:
            if cand in matched_gt:
                continue
            if partial and not is_similar(pred_entry_norm, gt_norm[cand], ("REFERENCE", "CITATION")):
                continue
            if not partial and any(pred_entry_norm.get(k) != gt_norm[cand].get(k) for k in ("REFERENCE", "CITATION")):
                continue

            # Additional keys check
            if additional_keys:
                add_ok = True
                for ak in additional_keys:
                    left = pred_entry_norm.get(ak, "")
                    right = gt_norm[cand].get(ak, "")
                    if isinstance(left, list):
                        left = " ".join(map(str, left))
                    if isinstance(right, list):
                        right = " ".join(map(str, right))
                    if partial:
                        if fuzzy_similar(left, right) <= ADDITIONAL_KEY_SIM_THRESHOLD:
                            add_ok = False
                            break
                    else:
                        if left != right:
                            add_ok = False
                            break
                fully_matched = add_ok
            found = cand
            break

        # Fallback scan
        if not found:
            for cand in gt_keys_all - matched_gt:
                if partial and not is_similar(pred_entry_norm, gt_norm[cand], ("REFERENCE", "CITATION")):
                    continue
                if not partial and any(
                        pred_entry_norm.get(k) != gt_norm[cand].get(k) for k in ("REFERENCE", "CITATION")):
                    continue
                add_ok = True
                if additional_keys:
                    for ak in additional_keys:
                        left = pred_entry_norm.get(ak, "")
                        right = gt_norm[cand].get(ak, "")
                        if isinstance(left, list):
                            left = " ".join(map(str, left))
                        if isinstance(right, list):
                            right = " ".join(map(str, right))
                        if partial:
                            if fuzzy_similar(left, right) <= ADDITIONAL_KEY_SIM_THRESHOLD:
                                add_ok = False
                                break
                        else:
                            if left != right:
                                add_ok = False
                                break
                fully_matched = add_ok
                found = cand
                break

        if found:
            matched_gt.add(found)
            if additional_keys:
                if fully_matched:
                    matches[pred_k] = found
                else:
                    partial_matches[pred_k] = found
            else:
                matches[pred_k] = found
        else:
            unmatched_preds[pred_k] = pred_orig[pred_k]  # Original data

    # Use ORIGINAL data for reports
    unmatched_gt_keys = sorted(gt_keys_all - matched_gt)
    unmatched_gt = {k: gt_orig[k] for k in unmatched_gt_keys}

    num_matches = len(matches)
    num_partial = len(partial_matches) if additional_keys else 0
    num_mismatches = len(unmatched_preds)
    num_unmatched_gt = len(unmatched_gt)

    precision = num_matches / total_pred if total_pred > 0 else 0
    recall = num_matches / total_gt if total_gt > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall > 0 else 0

    report = {
        "summary": {
            "total_ground_truth": total_gt,
            "total_predictions": total_pred,
            "matches": num_matches,
            "mismatches": num_mismatches,
            "unmatched_ground_truth": num_unmatched_gt,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        },
        "detailed_results": {
            "matches": matches,  # pred_k -> gt_k (keys only)
            "unmatched_predictions": unmatched_preds,  # Original data
            "unmatched_ground_truth": unmatched_gt,  # Original data
        }
    }
    if additional_keys:
        report["summary"]["partial_matches"] = num_partial
        report["detailed_results"]["partial_matches"] = partial_matches

    return os.path.basename(gt_path), report

# ----------------------------
# Main driver
# ----------------------------
def main(dir_predictions, dir_ground_truth, output_file, partial=True, additional_keys=None):
    gt_files = Path(dir_ground_truth).rglob("*.json")
    if not gt_files:
        print("No ground truth JSON files found in:", dir_ground_truth)
        return

    # Build list of runnable args
    run_args = []
    for gt in gt_files:
        pred = os.path.join(dir_predictions, os.path.basename(gt))
        if os.path.exists(pred):
            run_args.append((pred, gt, partial, additional_keys))
        else:
            print("Prediction missing for:", gt)

    results = []
    for args in run_args:
        results.append(evaluate_file(*args))

    report = {}
    total_gt_instances = total_pred_instances = total_matches = total_mismatches = total_unmatched_gt = 0
    total_partial_matches = 0

    for name, res in results:
        report[name] = res
        s = res["summary"]
        total_gt_instances += s["total_ground_truth"]
        total_pred_instances += s["total_predictions"]
        total_matches += s["matches"]
        total_mismatches += s["mismatches"]
        total_unmatched_gt += s["unmatched_ground_truth"]
        if "partial_matches" in s:
            total_partial_matches += s["partial_matches"]

    # global summary
    global_precision = total_matches / total_pred_instances if total_pred_instances else 0
    global_recall = total_matches / total_gt_instances if total_gt_instances else 0
    global_f1 = (2 * global_precision * global_recall / (global_precision + global_recall)) if (global_precision + global_recall) else 0

    report["comprehensive_summary"] = {
        "total_ground_truth": total_gt_instances,
        "total_predictions": total_pred_instances,
        "matches": total_matches,
        "mismatches": total_mismatches,
        "unmatched_ground_truth": total_unmatched_gt,
        "precision": round(global_precision, 4),
        "recall": round(global_recall, 4),
        "f1_score": round(global_f1, 4)
    }
    if additional_keys:
        report["comprehensive_summary"]["partial_matches"] = total_partial_matches

    with open(output_file, "w", encoding="utf8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print(f"Report saved to {output_file}")


# ----------------------------
# CLI
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fast evaluation for citation/context extraction JSONs")
    parser.add_argument("predictions_dir", help="Directory with prediction JSON files")
    parser.add_argument("ground_truth_dir", help="Directory with ground truth JSON files")
    parser.add_argument("output_file", help="Output JSON report path")
    parser.add_argument("--partial", action="store_true", help="Use partial (semantic) matching mode; otherwise exact")
    parser.add_argument("--add-keys", nargs="+", default=None, help="Additional keys to require for full match (e.g., SECTION)")

    args = parser.parse_args()

    main(args.predictions_dir, args.ground_truth_dir, args.output_file, partial=args.partial,
         additional_keys=args.add_keys)
