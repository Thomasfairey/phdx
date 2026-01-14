"""
DNA Engine - Linguistic Fingerprint Analyzer for PHDx

This module analyzes .docx files to extract the author's unique writing style,
creating a linguistic profile for maintaining consistency across thesis drafts.
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

import anthropic
from docx import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DRAFTS_DIR = Path(__file__).parent.parent / "drafts"
DATA_DIR = Path(__file__).parent.parent / "data"
DNA_OUTPUT_PATH = DATA_DIR / "author_dna.json"

# Hedging phrases commonly used in academic writing
HEDGING_PHRASES = [
    "it suggests",
    "arguably",
    "potentially",
    "perhaps",
    "possibly",
    "might",
    "may",
    "could",
    "appears to",
    "seems to",
    "tends to",
    "it is possible",
    "it is likely",
    "to some extent",
    "in some cases",
    "generally",
    "typically",
    "often",
    "usually",
    "somewhat",
    "relatively",
    "approximately",
    "indicates that",
    "suggests that",
    "implies that",
    "would appear",
    "it could be argued",
    "one might argue",
    "there is evidence",
    "the data suggests",
]

# Common academic transition words/phrases
TRANSITION_CATEGORIES = {
    "addition": ["furthermore", "moreover", "additionally", "in addition", "also", "besides"],
    "contrast": ["however", "nevertheless", "nonetheless", "conversely", "on the other hand", "whereas", "although", "despite"],
    "cause_effect": ["therefore", "consequently", "thus", "hence", "as a result", "accordingly"],
    "sequence": ["firstly", "secondly", "subsequently", "finally", "initially", "previously", "thereafter"],
    "emphasis": ["indeed", "notably", "significantly", "importantly", "crucially", "particularly"],
    "example": ["for instance", "for example", "specifically", "namely", "such as", "in particular"],
    "conclusion": ["in conclusion", "to summarize", "overall", "in summary", "ultimately", "to conclude"],
}


def load_docx_files(drafts_dir: Path = DRAFTS_DIR) -> list[dict]:
    """
    Load all .docx files from the drafts directory.

    Returns:
        List of dicts with 'filename' and 'content' keys.
    """
    documents = []

    if not drafts_dir.exists():
        print(f"Drafts directory not found: {drafts_dir}")
        return documents

    for docx_file in drafts_dir.glob("*.docx"):
        try:
            doc = Document(docx_file)
            full_text = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text.strip())

            documents.append({
                "filename": docx_file.name,
                "content": "\n".join(full_text)
            })
            print(f"Loaded: {docx_file.name}")

        except Exception as e:
            print(f"Error loading {docx_file.name}: {e}")

    return documents


def calculate_sentence_complexity(text: str) -> dict:
    """
    Calculate sentence complexity metrics.

    Returns:
        Dict with average_length, std_deviation, and length_distribution.
    """
    # Split into sentences (basic approach)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 2]

    if not sentences:
        return {"average_length": 0, "total_sentences": 0, "length_distribution": {}}

    lengths = [len(s.split()) for s in sentences]
    avg_length = sum(lengths) / len(lengths)

    # Categorize sentence lengths
    distribution = {
        "short (1-10 words)": len([l for l in lengths if l <= 10]),
        "medium (11-20 words)": len([l for l in lengths if 11 <= l <= 20]),
        "long (21-30 words)": len([l for l in lengths if 21 <= l <= 30]),
        "very_long (31+ words)": len([l for l in lengths if l > 30]),
    }

    return {
        "average_length": round(avg_length, 2),
        "total_sentences": len(sentences),
        "length_distribution": distribution
    }


def analyze_hedging_frequency(text: str) -> dict:
    """
    Analyze the frequency of hedging language in the text.

    Returns:
        Dict with hedging phrases found and their frequencies.
    """
    text_lower = text.lower()
    word_count = len(text.split())

    hedging_found = {}
    total_hedges = 0

    for phrase in HEDGING_PHRASES:
        count = text_lower.count(phrase)
        if count > 0:
            hedging_found[phrase] = count
            total_hedges += count

    # Calculate hedging density (per 1000 words)
    hedging_density = (total_hedges / word_count * 1000) if word_count > 0 else 0

    return {
        "phrases_found": hedging_found,
        "total_hedges": total_hedges,
        "hedging_density_per_1000_words": round(hedging_density, 2),
        "word_count": word_count
    }


def extract_transition_vocabulary(text: str) -> dict:
    """
    Extract and categorize transition vocabulary usage.

    Returns:
        Dict with transition words by category and frequencies.
    """
    text_lower = text.lower()
    word_count = len(text.split())

    transitions_by_category = {}
    total_transitions = 0

    for category, phrases in TRANSITION_CATEGORIES.items():
        category_matches = {}
        for phrase in phrases:
            count = text_lower.count(phrase)
            if count > 0:
                category_matches[phrase] = count
                total_transitions += count

        if category_matches:
            transitions_by_category[category] = category_matches

    # Calculate transition density
    transition_density = (total_transitions / word_count * 1000) if word_count > 0 else 0

    return {
        "by_category": transitions_by_category,
        "total_transitions": total_transitions,
        "transition_density_per_1000_words": round(transition_density, 2),
        "preferred_categories": sorted(
            transitions_by_category.keys(),
            key=lambda c: sum(transitions_by_category[c].values()),
            reverse=True
        )[:3] if transitions_by_category else []
    }


def analyze_with_claude(combined_text: str, client: anthropic.Anthropic) -> dict:
    """
    Use Claude 3.5 Sonnet to perform deep linguistic analysis.

    Returns:
        Dict with Claude's analysis of the writing style.
    """
    # Truncate if too long (keeping ~100k tokens worth)
    max_chars = 300000
    if len(combined_text) > max_chars:
        combined_text = combined_text[:max_chars] + "\n[Text truncated for analysis...]"

    prompt = f"""Analyze the following academic writing samples to create a detailed linguistic fingerprint of the author. Focus on:

1. **Writing Voice & Tone**: Is it formal, semi-formal? First person or third person dominant? Passive vs active voice preference?

2. **Sentence Structure Patterns**: Identify characteristic sentence constructions, use of complex vs simple sentences, and any notable syntactic preferences.

3. **Academic Register**: How does the author balance accessibility with scholarly tone? Note any discipline-specific conventions.

4. **Argumentation Style**: How does the author build arguments? Deductive, inductive, or mixed? How are claims qualified?

5. **Characteristic Phrases**: Identify any recurring phrases, expressions, or verbal tics unique to this author.

6. **Paragraph Organization**: How does the author typically structure paragraphs? Topic sentence patterns?

Provide your analysis as a structured JSON object with these categories. Be specific and provide examples where possible.

TEXT SAMPLES:
{combined_text}

Respond with ONLY a valid JSON object, no additional text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = response.content[0].text

        # Try to parse as JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, return as raw analysis
            return {"raw_analysis": response_text}

    except Exception as e:
        return {"error": str(e)}


def generate_author_dna(drafts_dir: Path = DRAFTS_DIR, output_path: Path = DNA_OUTPUT_PATH) -> Optional[dict]:
    """
    Main function to generate the complete author DNA profile.

    Returns:
        Complete DNA profile dict, or None if no documents found.
    """
    print("=" * 60)
    print("PHDx DNA Engine - Linguistic Fingerprint Analyzer")
    print("=" * 60)

    # Load documents
    print("\n[1/5] Loading documents from drafts folder...")
    documents = load_docx_files(drafts_dir)

    if not documents:
        print("No .docx files found in drafts folder. Please add thesis drafts.")
        return None

    print(f"Loaded {len(documents)} document(s)")

    # Combine all text for analysis
    combined_text = "\n\n---\n\n".join([
        f"[{doc['filename']}]\n{doc['content']}"
        for doc in documents
    ])

    total_words = len(combined_text.split())
    print(f"Total word count: {total_words:,}")

    # Analyze sentence complexity
    print("\n[2/5] Analyzing sentence complexity...")
    sentence_analysis = calculate_sentence_complexity(combined_text)
    print(f"Average sentence length: {sentence_analysis['average_length']} words")

    # Analyze hedging frequency
    print("\n[3/5] Analyzing hedging frequency...")
    hedging_analysis = analyze_hedging_frequency(combined_text)
    print(f"Hedging density: {hedging_analysis['hedging_density_per_1000_words']} per 1000 words")

    # Extract transition vocabulary
    print("\n[4/5] Extracting transition vocabulary...")
    transition_analysis = extract_transition_vocabulary(combined_text)
    print(f"Preferred transition categories: {', '.join(transition_analysis['preferred_categories'])}")

    # Claude deep analysis
    print("\n[5/5] Performing deep linguistic analysis with Claude...")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
        claude_analysis = analyze_with_claude(combined_text, client)
        print("Claude analysis complete")
    else:
        print("Warning: ANTHROPIC_API_KEY not set. Skipping Claude analysis.")
        claude_analysis = {"error": "API key not configured"}

    # Compile DNA profile
    dna_profile = {
        "metadata": {
            "documents_analyzed": [doc["filename"] for doc in documents],
            "total_word_count": total_words,
            "analysis_version": "1.0"
        },
        "sentence_complexity": sentence_analysis,
        "hedging_analysis": hedging_analysis,
        "transition_vocabulary": transition_analysis,
        "claude_deep_analysis": claude_analysis
    }

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dna_profile, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"DNA profile saved to: {output_path}")
    print("=" * 60)

    return dna_profile


if __name__ == "__main__":
    # Ensure drafts directory exists
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    # Run the analysis
    profile = generate_author_dna()

    if profile:
        print("\nProfile Summary:")
        print(f"  - Documents: {len(profile['metadata']['documents_analyzed'])}")
        print(f"  - Words: {profile['metadata']['total_word_count']:,}")
        print(f"  - Avg sentence: {profile['sentence_complexity']['average_length']} words")
        print(f"  - Hedging density: {profile['hedging_analysis']['hedging_density_per_1000_words']}/1000 words")
