"""
Lightweight RAG Evaluation Script (CPU-Friendly)
Uses: ROUGE, BLEU, METEOR (no heavy models)
Optional: Groq API for faithfulness check
"""

import os
import csv
import json
import numpy as np
from typing import List, Dict, Any
from groq import Groq

# Lightweight metrics
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
import nltk

# Ensure NLTK data
def ensure_nltk_data():
    """Download required NLTK data"""
    required = ['wordnet', 'punkt', 'averaged_perceptron_tagger']
    for package in required:
        try:
            nltk.data.find(f'tokenizers/{package}')
        except LookupError:
            print(f"⬇️  Downloading NLTK {package}...")
            nltk.download(package, quiet=True)
    print("✅ NLTK data ready.")

ensure_nltk_data()

# ===========================
# LIGHTWEIGHT METRICS
# ===========================

def calculate_rouge(reference: str, hypothesis: str) -> Dict[str, float]:
    """Calculate ROUGE-L F1 score"""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return {
        'rouge_l_precision': scores['rougeL'].precision,
        'rouge_l_recall': scores['rougeL'].recall,
        'rouge_l_f1': scores['rougeL'].fmeasure
    }

def calculate_bleu(reference: str, hypothesis: str) -> float:
    """Calculate BLEU score with smoothing"""
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    
    # Use smoothing to handle short sequences
    smooth = SmoothingFunction().method1
    return sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smooth)

def calculate_meteor(reference: str, hypothesis: str) -> float:
    """Calculate METEOR score"""
    try:
        ref_tokens = nltk.word_tokenize(reference.lower())
        hyp_tokens = nltk.word_tokenize(hypothesis.lower())
        return meteor_score([ref_tokens], hyp_tokens)
    except:
        return 0.0

def calculate_exact_match(reference: str, hypothesis: str) -> float:
    """Simple exact match after normalization"""
    ref_clean = ' '.join(reference.lower().split())
    hyp_clean = ' '.join(hypothesis.lower().split())
    return 1.0 if ref_clean == hyp_clean else 0.0

def calculate_word_overlap(reference: str, hypothesis: str) -> float:
    """Calculate word-level overlap (simple F1)"""
    ref_words = set(reference.lower().split())
    hyp_words = set(hypothesis.lower().split())
    
    if not ref_words or not hyp_words:
        return 0.0
    
    intersection = ref_words & hyp_words
    precision = len(intersection) / len(hyp_words) if hyp_words else 0
    recall = len(intersection) / len(ref_words) if ref_words else 0
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1

# ===========================
# GROQ FAITHFULNESS CHECK
# ===========================

def check_faithfulness_groq(query: str, context: str, response: str, api_key: str) -> Dict[str, Any]:
    """
    Use Groq API to check if response is faithful to context.
    Uses lightweight llama-3.1-8b model.
    """
    try:
        client = Groq(api_key=api_key)
        
        prompt = f"""You are an AI judge evaluating RAG system responses.

**Task**: Determine if the RESPONSE is faithful to the CONTEXT provided.

**CONTEXT**:
{context[:2000]}  

**USER QUERY**: {query}

**RESPONSE**: {response}

**Instructions**:
1. Check if the response contains information NOT found in the context (hallucination)
2. Check if the response contradicts the context
3. Assign a faithfulness score from 0.0 to 1.0:
   - 1.0 = Fully faithful, all info from context
   - 0.5 = Partially faithful, some external knowledge used
   - 0.0 = Completely unfaithful, made up information

Respond in JSON format:
{{
  "faithfulness_score": <float 0.0-1.0>,
  "reasoning": "<brief explanation>",
  "hallucinations": ["<list any hallucinated facts>"]
}}
"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fixed model name
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        print(f"⚠️  Faithfulness check failed: {e}")
        return {
            "faithfulness_score": 0.5,
            "reasoning": "Error occurred",
            "hallucinations": []
        }

# ===========================
# MAIN EVALUATION
# ===========================

def evaluate_single_response(
    query: str,
    reference: str,
    hypothesis: str,
    context: str,
    api_key: str = None
) -> Dict[str, Any]:
    """Evaluate a single RAG response"""
    
    metrics = {}
    
    # 1. Lightweight n-gram metrics
    rouge_scores = calculate_rouge(reference, hypothesis)
    metrics.update(rouge_scores)
    
    metrics['bleu'] = calculate_bleu(reference, hypothesis)
    metrics['meteor'] = calculate_meteor(reference, hypothesis)
    metrics['exact_match'] = calculate_exact_match(reference, hypothesis)
    metrics['word_overlap_f1'] = calculate_word_overlap(reference, hypothesis)
    
    # 2. Optional: Faithfulness check via Groq
    if api_key:
        faithfulness_result = check_faithfulness_groq(query, context, hypothesis, api_key)
        metrics['faithfulness_score'] = faithfulness_result.get('faithfulness_score', 0.5)
        metrics['faithfulness_reasoning'] = faithfulness_result.get('reasoning', '')
        metrics['hallucinations'] = len(faithfulness_result.get('hallucinations', []))
    else:
        metrics['faithfulness_score'] = None
        metrics['faithfulness_reasoning'] = "Skipped (no API key)"
        metrics['hallucinations'] = None
    
    return metrics

def load_evaluation_data(csv_path: str = "evaluation_results.csv") -> List[Dict]:
    """Load evaluation results from CSV"""
    results = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Print available columns for debugging
        first_row = next(reader)
        print(f"📋 CSV Columns found: {list(first_row.keys())}\n")
        
        # Try to map common column name variations
        query_col = None
        reference_col = None
        hypothesis_col = None
        context_col = None
        
        # Check for different possible column names
        columns = list(first_row.keys())
        for col in columns:
            col_lower = col.lower().strip()
            if 'query' in col_lower or 'question' in col_lower:
                query_col = col
            elif 'ground' in col_lower or 'reference' in col_lower or 'truth' in col_lower:
                reference_col = col
            elif 'response' in col_lower or 'answer' in col_lower or 'prediction' in col_lower:
                hypothesis_col = col
            elif 'context' in col_lower or 'retrieved' in col_lower:
                context_col = col
        
        if not query_col or not reference_col or not hypothesis_col:
            print("❌ Error: Could not find required columns!")
            print(f"   Looking for: query/question, ground_truth/reference, response/answer")
            print(f"   Found columns: {columns}")
            raise ValueError("Missing required columns in CSV")
        
        print(f"✅ Mapped columns:")
        print(f"   Query:      {query_col}")
        print(f"   Reference:  {reference_col}")
        print(f"   Hypothesis: {hypothesis_col}")
        print(f"   Context:    {context_col or 'Not found (will use empty string)'}\n")
        
        # Process first row
        results.append({
            'query': first_row[query_col],
            'reference': first_row[reference_col],
            'hypothesis': first_row[hypothesis_col],
            'context': first_row.get(context_col, '') if context_col else ''
        })
        
        # Process remaining rows
        for row in reader:
            results.append({
                'query': row[query_col],
                'reference': row[reference_col],
                'hypothesis': row[hypothesis_col],
                'context': row.get(context_col, '') if context_col else ''
            })
    
    return results

def judge_the_results(api_key: str = None, input_csv: str = "evaluation_results.csv"):
    """Main evaluation function"""
    
    print(f"\n🔎 Loading results from {input_csv}...")
    data = load_evaluation_data(input_csv)
    print(f"✅ Loaded {len(data)} responses to evaluate.\n")
    
    if not api_key:
        print("⚠️  No GROQ_API_KEY provided. Faithfulness check will be skipped.")
        print("   Set environment variable: export GROQ_API_KEY='your_key'\n")
    
    all_metrics = []
    
    for i, item in enumerate(data, 1):
        print(f"⚖️  Evaluating {i}/{len(data)}...", end='\r')
        
        metrics = evaluate_single_response(
            query=item['query'],
            reference=item['reference'],
            hypothesis=item['hypothesis'],
            context=item['context'],
            api_key=api_key
        )
        
        all_metrics.append(metrics)
    
    print(f"\n✅ Evaluation complete!\n")
    
    # Calculate averages
    avg_metrics = {}
    for key in all_metrics[0].keys():
        if key in ['faithfulness_reasoning']:
            continue
        
        values = [m[key] for m in all_metrics if m[key] is not None]
        if values:
            avg_metrics[f"avg_{key}"] = np.mean(values)
    
    # Print results
    print("=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)
    
    print("\n📈 N-gram Overlap Metrics:")
    print(f"  ROUGE-L F1:       {avg_metrics.get('avg_rouge_l_f1', 0):.4f}")
    print(f"  BLEU:             {avg_metrics.get('avg_bleu', 0):.4f}")
    print(f"  METEOR:           {avg_metrics.get('avg_meteor', 0):.4f}")
    print(f"  Word Overlap F1:  {avg_metrics.get('avg_word_overlap_f1', 0):.4f}")
    print(f"  Exact Match:      {avg_metrics.get('avg_exact_match', 0):.4f}")
    
    if api_key:
        print("\n🤖 LLM-Based Metrics:")
        print(f"  Faithfulness:     {avg_metrics.get('avg_faithfulness_score', 0):.4f}")
        print(f"  Avg Hallucinations: {avg_metrics.get('avg_hallucinations', 0):.2f}")
    
    print("\n" + "=" * 60)
    
    # Save detailed results
    output_file = "evaluation_metrics.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(all_metrics[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_metrics)
    
    print(f"\n💾 Detailed metrics saved to: {output_file}")
    
    # Save summary
    summary_file = "evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(avg_metrics, f, indent=2)
    
    print(f"💾 Summary saved to: {summary_file}\n")

# ===========================
# ENTRY POINT
# ===========================

if __name__ == "__main__":
    api_key = os.getenv("GROQ_API_KEY")
    judge_the_results(api_key=api_key)