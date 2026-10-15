import streamlit as st
from transformers import pipeline


@st.cache_resource
def load_classifier():
    return pipeline(
        "image-classification",
        model="watersplash/waste-classification",
        device=-1,
    )


def classify_image(image):
    classifier = load_classifier()
    results = classifier(image, top_k=3)

    best = results[0]

    return {
        "category": best["label"],
        "confidence": float(best["score"]),
        "alternatives": results,
    }