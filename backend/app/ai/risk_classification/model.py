from transformers import AutoModelForSequenceClassification

MODEL_NAME = "roberta-base"


def load_risk_classifier():
    return AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=3,
    )
