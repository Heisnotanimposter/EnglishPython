from transformers import DistilBertTokenizer, DistilBertForMaskedLM
import torch
import language_tool_python

def load_model_and_tokenizer():
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    model = DistilBertForMaskedLM.from_pretrained('distilbert-base-uncased')
    return model, tokenizer

def grammar_correction(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    if not matches:
        return text  # No errors were found

    # Load the transformer model and tokenizer
    model, tokenizer = load_model_and_tokenizer()
    model.eval()

    corrected_text = text
    for match in reversed(matches):  # Reverse to not disrupt indices of corrections
        start = match.offset
        end = match.offset + match.errorLength
        incorrect_phrase = text[start:end]
        # Generate replacement using masked language model prediction
        prompt_text = text[:start] + '[MASK]' + text[end:]
        inputs = tokenizer.encode(prompt_text, return_tensors='pt')
        with torch.no_grad():
            predictions = model(inputs)[0]
        predicted_index = torch.argmax(predictions[0, start]).item()
        predicted_token = tokenizer.convert_ids_to_tokens([predicted_index])[0]
        corrected_text = corrected_text[:start] + predicted_token + corrected_text[end:]

    return corrected_text
# Example usage
if __name__ == "__main__":
    input_text = ("The topic is basically about the methods of childhood educational effects. "
                  "At the first of view, the opinion of allowing children to make their own "
                  "choice on every matters would make the children become more automatic, "
                  "active, and for their parent, it would be contains more risk to manage them. "
                  "Because, if children take the entire orders belonging to them, they would buy "
                  "chocolate, toys, fancy clothes, game machines, instead of healthy food or "
                  "educational books.")
    score, corrections = check_grammar(input_text)
    print(f"Your grammar score is {score}/100")
    print("Correction List:")
    for correction in corrections:
        print(f"\nMessage: {correction['Message']}")
        print(f"Incorrect Text: {correction['Incorrect Text']}")
        print(f"Suggested Corrections: {correction['Suggested Corrections']}")
        print(f"Context: {correction['Context']}")
