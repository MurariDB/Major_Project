# filename: evaluate.py
import pandas as pd
import os
from tqdm import tqdm
from main import VoiceRAGAssistant 

def run_evaluation_questions(assistant):
    dataset_path = "test_dataset.csv"
    if not os.path.exists(dataset_path):
        print(f"❌ Error: {dataset_path} not found")
        return
    
    test_df = pd.read_csv(dataset_path)
    questions = test_df["question"].tolist()
    ground_truths = test_df["ground_truth"].tolist()
    
    results = []
    print(f"\n🚀 Running evaluation on {len(questions)} questions...")
    
    # We use tqdm to show a progress bar
    for question, ground_truth in tqdm(zip(questions, ground_truths), total=len(questions)):
        # Call the updated main.py function
        result = assistant.process_text_query(question, speak_response=False)
        
        results.append({
            "question": question,
            "answer": result.get("response", ""),
            "contexts": result.get("contexts", []), # Now this will actually capture data!
            "ground_truth": ground_truth
        })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv("evaluation_results.csv", index=False)
    print(f"\n✅ Results saved to: evaluation_results.csv (Now with contexts!)")

if __name__ == "__main__":
    pdf_folder = "data/pdfs" # Ensure this matches your folder name
    if not os.path.isdir(pdf_folder):
        print(f"❌ Error: Folder '{pdf_folder}' not found.")
    else:
        print("🚀 Initializing...")
        assistant = VoiceRAGAssistant()
        assistant.ingest_documents(pdf_dir=pdf_folder)
        run_evaluation_questions(assistant)