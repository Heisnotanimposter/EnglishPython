# EnglishPython
 English text grammer recognition and recommand fix, Recognition of Eng speaking Python

# Grammar Correction Tool

This project implements a grammar correction tool using `language_tool_python` for detecting grammatical errors and the `transformers` library featuring `DistilBertForMaskedLM` to suggest corrections based on the context of the sentences. It aims to provide a utility for enhancing writing by identifying and suggesting corrections for grammatical mistakes in English text.

## Features

- **Grammar Checking**: Leverages LanguageTool to detect grammatical errors in English text.
- **Contextual Corrections**: Utilizes a distilled version of BERT (DistilBERT) from the `transformers` library to understand context and suggest accurate corrections.
- **Python Integration**: Easy to integrate with other Python applications and services for text processing and correction.

## Installation

Ensure you have Python 3.6+ installed on your system. You can install the required dependencies via pip:

```bash
pip install transformers torch language_tool_python

from grammar_correction import grammar_correction

input_text = "Input your text here to check for grammatical errors."
corrected_text = grammar_correction(input_text)
print("Corrected Text:", corrected_text)

python grammar_correction.py