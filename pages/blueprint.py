import streamlit as st
import pandas as pd

st.set_page_config(page_title="Question Paper Blueprint Generator", layout="wide")

st.title("📘 Question Paper Blueprint Generator")
st.caption("Q1–Q3: 5×1M | Q4–Q10: (i) 2M, (ii) 3M")

# -------------------------
# CONFIG
# -------------------------
UNITS = [
    "Unit 8: Application of Percentages",
    "Unit 9: Rational Numbers",
    "Unit 10: Algebraic Expressions & Equations",
    "Unit 11: Mensuration",
    "Unit 12: Sets",
    "Unit 13: Probability"
]

DIFFICULTY = ["Easy", "Medium", "HOTS"]
Q_TYPE = ["Objective", "Subjective"]

question_data = []

st.subheader("📝 Question Tagging")

# -------------------------
# Q1 to Q3 (5 sub-questions of 1 mark each)
# -------------------------
for q in range(1, 4):
    with st.container(border=True):
        st.markdown(f"### Question {q} (5 × 1 Mark)")

        for i in range(1, 6):
            col1, col2, col3, col4 = st.columns(4)

            unit = col1.selectbox(
                "Unit",
                ["Select"] + UNITS,
                key=f"unit_{q}_{i}"
            )

            difficulty = col2.selectbox(
                "Difficulty",
                DIFFICULTY,
                key=f"diff_{q}_{i}"
            )

            col3.selectbox(
                "Marks",
                [1],
                key=f"marks_{q}_{i}"
            )

            q_type = col4.selectbox(
                "Question Type",
                Q_TYPE,
                key=f"type_{q}_{i}"
            )

            if unit != "Select":
                question_data.append({
                    "Question": f"Q{q}({i})",
                    "Unit": unit,
                    "Difficulty": difficulty,
                    "Marks": 1,
                    "Type": q_type
                })

# -------------------------
# Q4 to Q10 (2M + 3M)
# -------------------------
for q in range(4, 11):
    with st.container(border=True):
        st.markdown(f"### Question {q}")

        # (i) – 2 Marks
        st.markdown("**(i) – 2 Marks**")
        col1, col2, col3, col4 = st.columns(4)

        unit_i = col1.selectbox("Unit", ["Select"] + UNITS, key=f"unit_{q}a")
        diff_i = col2.selectbox("Difficulty", DIFFICULTY, key=f"diff_{q}a")
        col3.selectbox("Marks", [2], key=f"marks_{q}a")
        type_i = col4.selectbox("Question Type", Q_TYPE, key=f"type_{q}a")

        if unit_i != "Select":
            question_data.append({
                "Question": f"Q{q}(i)",
                "Unit": unit_i,
                "Difficulty": diff_i,
                "Marks": 2,
                "Type": type_i
            })

        st.divider()

        # (ii) – 3 Marks
        st.markdown("**(ii) – 3 Marks**")
        col1, col2, col3, col4 = st.columns(4)

        unit_ii = col1.selectbox("Unit", ["Select"] + UNITS, key=f"unit_{q}b")
        diff_ii = col2.selectbox("Difficulty", DIFFICULTY, key=f"diff_{q}b")
        col3.selectbox("Marks", [3], key=f"marks_{q}b")
        type_ii = col4.selectbox("Question Type", Q_TYPE, key=f"type_{q}b")

        if unit_ii != "Select":
            question_data.append({
                "Question": f"Q{q}(ii)",
                "Unit": unit_ii,
                "Difficulty": diff_ii,
                "Marks": 3,
                "Type": type_ii
            })

# -------------------------
# DATA PROCESSING
# -------------------------
if question_data:
    df = pd.DataFrame(question_data)

    st.subheader("📊 Question Mapping Preview")
    st.dataframe(df, use_container_width=True)

    blueprint = (
        df.groupby(["Unit", "Marks"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for m in [1, 2, 3]:
        if m not in blueprint.columns:
            blueprint[m] = 0

    blueprint["Total Marks"] = (
        blueprint[1] * 1 +
        blueprint[2] * 2 +
        blueprint[3] * 3
    )

    blueprint = blueprint.rename(columns={
        1: "1 Mark",
        2: "2 Marks",
        3: "3 Marks"
    })

    st.subheader("📘 Blueprint Summary")
    st.dataframe(blueprint, use_container_width=True)

    st.success(f"✅ Total Marks Covered: {blueprint['Total Marks'].sum()}")

    st.download_button(
        "📥 Download Blueprint CSV",
        blueprint.to_csv(index=False),
        file_name="Blueprint_Summary.csv",
        mime="text/csv"
    )

    st.download_button(
        "📥 Download Question Mapping CSV",
        df.to_csv(index=False),
        file_name="Question_Mapping.csv",
        mime="text/csv"
    )
else:
    st.info("ℹ Please tag questions to generate blueprint.")
