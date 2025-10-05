import json
from opti_scout.build_model import ModelBuilder
from opti_scout.classes import AssigningActivititesProblem
import streamlit as st


def main():
    st.title("Scout group activity allocation")
    st.sidebar.header("Navigation")
    option = st.sidebar.radio(" ", ("Application", "Documentation"))

    if option == "Application":
        uploaded_file = st.file_uploader("Get input file (.json)", type="json")
        if uploaded_file is not None:
            data = json.load(uploaded_file)
            assigning_activities_problem = AssigningActivititesProblem.from_json(data)
            st.write(assigning_activities_problem.summarize())
            is_optimize = st.button("Optimize")
            if is_optimize:
                model_builder = ModelBuilder.create(assigning_activities_problem)
                solution = model_builder.solve()
                st.header("Layout")
                if solution.is_valid():
                    st.write(solution.create_gantt_chart())
                else:
                    st.write(f"The problem was not solved, got the following status {solution.status}")

    if option == "Documentation":
        with open("README.md", "r") as file:
            st.write(file.read())


if __name__ == "__main__":
    main()
