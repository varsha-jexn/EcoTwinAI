import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

from data import bins
from digital_twin import (
    get_status,
    calculate_priority,
    update_bin,
    get_priority_order,
    simulate_collection,
)
from waste_classifier import classify_image
from ai_advisor import generate_advice


st.set_page_config(
    page_title="EcoTwin AI",
    page_icon="♻️",
    layout="wide",
)

st.title("♻️ EcoTwin AI")
st.subheader("Smart Waste Management Digital Twin")

st.caption(
    "Prototype using simulated bin readings "
    "and AI-assisted waste classification."
)


# ---------- INITIALIZE APP STATE ----------

if "bins" not in st.session_state:
    st.session_state.bins = [
        dict(item) for item in bins
    ]

if "waste_records" not in st.session_state:
    st.session_state.waste_records = []

if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None


def refresh_bin_calculations():
    for item in st.session_state.bins:
        item["status"] = get_status(
            item["fill_level"]
        )
        item["priority"] = calculate_priority(
            item["fill_level"],
            item["hours_since_collection"],
        )


refresh_bin_calculations()
current_bins = st.session_state.bins


# ---------- DASHBOARD METRICS ----------

st.header("City Overview")

total_bins = len(current_bins)

urgent_count = sum(
    item["status"] == "Urgent"
    for item in current_bins
)

average_fill = sum(
    item["fill_level"]
    for item in current_bins
) / max(total_bins, 1)

c1, c2, c3 = st.columns(3)

c1.metric("Total Virtual Bins", total_bins)
c2.metric("Urgent Bins", urgent_count)
c3.metric("Average Fill", f"{average_fill:.1f}%")


# ---------- INTERACTIVE DIGITAL TWIN ----------

st.divider()
st.header("1. Interactive Digital Twin")

selected_id = st.selectbox(
    "Choose a virtual bin",
    [item["id"] for item in current_bins],
)

selected_bin = next(
    item for item in current_bins
    if item["id"] == selected_id
)

st.write(
    f"Location: {selected_bin['location']} | "
    f"Assigned waste: {selected_bin['waste_type']}"
)

new_fill = st.slider(
    "Simulated fill level (%)",
    min_value=0,
    max_value=100,
    value=int(selected_bin["fill_level"]),
    key=f"slider_{selected_id}",
)

if st.button("Update Digital Twin"):
    update_bin(selected_bin, new_fill)
    st.rerun()


# ---------- DIGITAL TWIN VISUALIZATION ----------

st.subheader("Virtual Bin Status")

df = pd.DataFrame(st.session_state.bins)

st.dataframe(
    df[
        [
            "id",
            "location",
            "waste_type",
            "fill_level",
            "status",
            "priority",
        ]
    ].sort_values(
        "priority",
        ascending=False,
    ),
    use_container_width=True,
    hide_index=True,
)

bar_chart = px.bar(
    df,
    x="location",
    y="fill_level",
    color="status",
    text="fill_level",
    range_y=[0, 100],
    title="Simulated Bin Fill Levels",
)

st.plotly_chart(
    bar_chart,
    use_container_width=True,
)

# Simplified virtual layout of the sample campus.
layout = {
    "BIN-01": (0, 2),
    "BIN-02": (1, 1),
    "BIN-03": (2, 2),
    "BIN-04": (3, 1),
    "BIN-05": (4, 2),
    "BIN-06": (5, 1),
}

df["x"] = df["id"].map(
    lambda item: layout[item][0]
)
df["y"] = df["id"].map(
    lambda item: layout[item][1]
)

map_chart = px.scatter(
    df,
    x="x",
    y="y",
    color="status",
    size="fill_level",
    text="id",
    hover_name="location",
    hover_data=["fill_level", "waste_type"],
    title="Virtual Campus Bin Layout",
    size_max=40,
)

map_chart.update_layout(
    xaxis_visible=False,
    yaxis_visible=False,
)

st.plotly_chart(
    map_chart,
    use_container_width=True,
)


# ---------- COMPUTER VISION ----------

st.divider()
st.header("2. Computer Vision Waste Scanner")

uploaded_image = st.file_uploader(
    "Upload a waste image",
    type=["jpg", "jpeg", "png", "webp"],
)

target_bin_id = st.selectbox(
    "Choose the bin to update after classification",
    [item["id"] for item in current_bins],
    key="target_bin",
)

if uploaded_image is not None:
    image = Image.open(uploaded_image).convert("RGB")
    st.image(
        image,
        caption="Uploaded waste image",
        use_container_width=True,
    )

    if st.button("Classify Image and Update Twin"):
        try:
            with st.spinner(
                "Loading model and classifying image..."
            ):
                prediction = classify_image(image)

            st.session_state.last_prediction = prediction

            # Record the classification.
            st.session_state.waste_records.append({
                "category": prediction["category"],
                "confidence": prediction["confidence"],
                "target_bin": target_bin_id,
            })

            # Update the selected virtual bin.
            target_bin = next(
                item for item in st.session_state.bins
                if item["id"] == target_bin_id
            )

            label = prediction["category"].lower()

            if "plastic" in label:
                target_bin["waste_type"] = "Plastic"
            elif "paper" in label or "cardboard" in label:
                target_bin["waste_type"] = "Paper"
            elif "metal" in label:
                target_bin["waste_type"] = "Metal"
            elif "glass" in label:
                target_bin["waste_type"] = "Glass"
            elif "biological" in label or "grass" in label:
                target_bin["waste_type"] = "Organic"
            else:
                target_bin["waste_type"] = "General"

            # Simulate a small increase in bin fill.
            target_bin["fill_level"] = min(
                100,
                target_bin["fill_level"] + 5,
            )

            refresh_bin_calculations()

            st.success(
                "Classification recorded and "
                "digital twin updated."
            )

        except Exception as error:
            st.error(
                "Classification failed. Check your internet "
                "connection, model download, and installed "
                "libraries. Details: " + str(error)
            )

if st.session_state.last_prediction is not None:
    prediction = st.session_state.last_prediction

    st.write(
        f"**Predicted category:** {prediction['category']}"
    )

    st.write(
        f"**Model confidence:** "
        f"{prediction['confidence']:.1%}"
    )

    st.caption(
        "Predictions can be incorrect. Verify the result "
        "before using it for actual waste disposal."
    )


# ---------- COLLECTION PRIORITY ----------

st.divider()
st.header("3. Smart Collection Priority")

ordered_bins = get_priority_order(
    st.session_state.bins
)

for rank, item in enumerate(ordered_bins, start=1):
    st.write(
        f"{rank}. **{item['id']} — {item['location']}** "
        f"| {item['fill_level']}% full "
        f"| {item['status']} "
        f"| Priority score: {item['priority']}"
    )


# ---------- WHAT-IF SIMULATION ----------

st.divider()
st.header("4. What-if Collection Simulator")

threshold = st.slider(
    "Collect bins at or above this fill level (%)",
    min_value=50,
    max_value=100,
    value=90,
)

if st.button("Simulate Collection"):
    st.session_state.simulated_bins = simulate_collection(
        st.session_state.bins,
        threshold=threshold,
    )

if "simulated_bins" in st.session_state:
    before = st.session_state.bins
    after = st.session_state.simulated_bins

    before_urgent = sum(
        item["fill_level"] >= 90
        for item in before
    )

    after_urgent = sum(
        item["fill_level"] >= 90
        for item in after
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Urgent bins before",
        before_urgent,
    )

    col2.metric(
        "Urgent bins after simulation",
        after_urgent,
        delta=after_urgent - before_urgent,
        delta_color="inverse",
    )

    st.dataframe(
        pd.DataFrame(after)[
            ["id", "location", "fill_level"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Scenario output is simulated. It is not a "
        "measurement of real-world performance."
    )


# ---------- GENERATIVE AI ADVISOR ----------

st.divider()
st.header("5. Generative AI Waste Advisor")

st.write(
    "Ask for an action plan based on the current "
    "simulated bin readings."
)

if st.button("Generate AI Recommendations"):
    try:
        with st.spinner("Generating recommendations..."):
            advice = generate_advice(
                st.session_state.bins
            )

        st.session_state.advice = advice

    except Exception as error:
        st.error(
            "AI request failed. Check your API key, "
            "account access, and internet connection. "
            + str(error)
        )

if "advice" in st.session_state:
    st.markdown(st.session_state.advice)


# ---------- FOOTER ----------

st.divider()

st.caption(
    "EcoTwin AI | Computer Vision + Digital Twin + "
    "Generative AI | Prototype using simulated bin data"
)