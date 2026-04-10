from transformers import AutoModelForSequenceClassification

MODEL_NAME = "bert-base-uncased"


def load_clause_classifier():
    return AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=6,
    )
