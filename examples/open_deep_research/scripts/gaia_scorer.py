import argparse
import json
import re
import string
import warnings


def normalize_number_str(number_str: str) -> float:
    # we replace these common units and commas to allow
    # conversion to float
    for char in ["$", "%", ","]:
        number_str = number_str.replace(char, "")
    try:
        return float(number_str)
    except ValueError:
        print(f"String {number_str} cannot be normalized to number str.")
        return float("inf")


def split_string(
    s: str,
    char_list: list[str] = [",", ";"],
) -> list[str]:
    pattern = f"[{''.join(char_list)}]"
    return re.split(pattern, s)


def is_float(element: any) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False


def question_scorer(
    model_answer: str,
    ground_truth: str,
) -> bool:
    if model_answer is None:
        model_answer = "None"
    # if gt is a number
    if is_float(ground_truth):
        normalized_answer = normalize_number_str(str(model_answer))
        return normalized_answer == float(ground_truth)

    # if gt is a list
    elif any(char in ground_truth for char in [",", ";"]):
        # question with the fish: normalization removes punct

        gt_elems = split_string(ground_truth)
        ma_elems = split_string(model_answer)

        # check length is the same
        if len(gt_elems) != len(ma_elems):
            warnings.warn("Answer lists have different lengths, returning False.", UserWarning)
            return False

        # compare each element as float or str
        comparisons = []
        for ma_elem, gt_elem in zip(ma_elems, gt_elems):
            if is_float(gt_elem):
                normalized_ma_elem = normalize_number_str(ma_elem)
                comparisons.append(normalized_ma_elem == float(gt_elem))
            else:
                # we do not remove punct since comparisons can include punct
                comparisons.append(
                    normalize_str(ma_elem, remove_punct=False) == normalize_str(gt_elem, remove_punct=False)
                )
        return all(comparisons)

    # if gt is a str
    else:
        return normalize_str(model_answer) == normalize_str(ground_truth)


def check_prediction_contains_answer_letters_in_order(prediction, true_answer):
    prediction = prediction.lower()
    true_answer = true_answer.lower()
    if len(prediction) > len(true_answer) * 3:
        return False
    i = 0
    for letter in true_answer:
        if letter in prediction[i:]:
            i += prediction[i:].index(letter)
        else:
            return False
    return True


def check_close_call(prediction, true_answer, is_correct):
    if is_correct:
        return True
    else:
        if is_float(true_answer):
            return is_correct
        else:
            if (
                check_prediction_contains_answer_letters_in_order(str(prediction), str(true_answer))
                and len(str(true_answer)) * 0.5 <= len(str(prediction)) <= len(str(true_answer)) * 2
            ):
                print(f"Close call: {prediction} vs {true_answer}")
                return True
            else:
                return False


def normalize_str(input_str, remove_punct=True) -> str:
    """
    Normalize a string by:
    - Removing all white spaces
    - Optionally removing punctuation (if remove_punct is True)
    - Converting to lowercase
    Parameters:
    - input_str: str, the string to normalize
    - remove_punct: bool, whether to remove punctuation (default: True)
    Returns:
    - str, the normalized string
    """
    # Remove all white spaces. Required e.g for seagull vs. sea gull
    no_spaces = re.sub(r"\s", "", input_str)

    # Remove punctuation, if specified.
    if remove_punct:
        translator = str.maketrans("", "", string.punctuation)
        return no_spaces.lower().translate(translator)
    else:
        return no_spaces.lower()


def exact_match(prediction: str, true_answer: str) -> bool:
    """
    Character-by-character exact match comparison.
    
    Parameters:
    - prediction: str, the model's prediction
    - true_answer: str, the ground truth answer
    
    Returns:
    - bool, True if predictions match exactly character-by-character
    """
    if prediction is None:
        prediction = "None"
    if true_answer is None:
        true_answer = "None"
    return str(prediction) == str(true_answer)


def score_results(input_file: str, output_file: str = None):
    """
    Score results from a JSONL file by computing exact match and quasi exact match metrics.
    
    Parameters:
    - input_file: str, path to input JSONL file with 'prediction' and 'true_answer' fields
    - output_file: str, optional path to output JSONL file with added 'exact_match' and 'quasi_exact_match' fields
    """
    exact_matches = 0
    quasi_exact_matches = 0
    total = 0
    results = []
    
    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                warnings.warn(f"Skipping invalid JSON on line {line_num}: {e}", UserWarning)
                continue
            
            if "prediction" not in entry:
                warnings.warn(f"Missing 'prediction' field on line {line_num}, skipping", UserWarning)
                continue
            if "true_answer" not in entry:
                warnings.warn(f"Missing 'true_answer' field on line {line_num}, skipping", UserWarning)
                continue
            
            prediction = entry["prediction"]
            true_answer = entry["true_answer"]
            
            # Compute exact match
            exact_match_result = exact_match(prediction, true_answer)
            if exact_match_result:
                exact_matches += 1
            
            # Compute quasi exact match
            quasi_exact_match_result = question_scorer(prediction, true_answer)
            if quasi_exact_match_result:
                quasi_exact_matches += 1
            
            total += 1
            
            # Add results to entry if output file is specified
            if output_file is not None:
                entry["exact_match"] = exact_match_result
                entry["quasi_exact_match"] = quasi_exact_match_result
                results.append(entry)
    
    # Print summary statistics
    print(f"\n{'='*60}")
    print(f"Scoring Results Summary")
    print(f"{'='*60}")
    print(f"Total examples: {total}")
    print(f"\nExact Match:")
    print(f"  Correct: {exact_matches}")
    print(f"  Accuracy: {exact_matches/total*100:.2f}%" if total > 0 else "  Accuracy: N/A")
    print(f"\nQuasi Exact Match:")
    print(f"  Correct: {quasi_exact_matches}")
    print(f"  Accuracy: {quasi_exact_matches/total*100:.2f}%" if total > 0 else "  Accuracy: N/A")
    print(f"{'='*60}\n")
    
    # Write detailed results if output file is specified
    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as f:
            for entry in results:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Detailed results written to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score agent results by computing exact match and quasi exact match metrics"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to input JSONL file with 'prediction' and 'true_answer' fields"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Optional path to output JSONL file with added 'exact_match' and 'quasi_exact_match' fields"
    )
    
    args = parser.parse_args()
    score_results(args.input_file, args.output)
