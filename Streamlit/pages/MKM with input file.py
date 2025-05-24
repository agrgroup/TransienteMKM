import os
import sys
import shutil
import streamlit as st
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from io import BytesIO
import networkx as nx
import zipfile

from inp_file_multiple import *
from graph_helper import *
from utility import *

# Constants
DOT_FILE_PATH = "run/networkplots/network_01_0298K.dot"
RESULT_FOLDER = "run/"
ZIP_OUTPUT_PATH = "single_run_run.zip"

# Set up Streamlit page
st.set_page_config(
    page_title="MKM Input File Generator and Solver",
    page_icon="👋",
    initial_sidebar_state="expanded"
)

st.title('e-MKM Solver')


def mkm_file_solver():
    st.header("MKM File Solver")

    uploaded_mkm_file = st.file_uploader("Upload MKM Input File", type="mkm")

    if not uploaded_mkm_file:
        return

    try:
        mkm_data = uploaded_mkm_file.read().decode("utf-8")
        st.success("MKM Input File Loaded Successfully!")
        st.text_area("Preview of MKM Input File", mkm_data, height=300)

        # Save to temp path
        temp_file_path = os.path.join(uploaded_mkm_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_mkm_file.getbuffer())

        if st.button("Run MKM Solver"):
            result_message, success = run_executable(temp_file_path)
            if success:
                st.success(result_message)
                coverage()
            else:
                st.error(result_message)

        # Reaction Network Visualization
        if st.button("Create Reaction Network Visualization"):
            if os.path.exists(DOT_FILE_PATH):
                graph = create_reaction_network_visualization(dot_file=DOT_FILE_PATH)
                if graph:
                    graph_svg = graph.pipe(format='svg').decode('utf-8')
                    st.image(graph_svg)
                    st.download_button(
                        label="Download Reaction Network (SVG)",
                        data=graph.pipe(format='svg'),
                        file_name="reaction_network.svg",
                        mime="image/svg+xml"
                    )
                else:
                    st.error("Failed to create graph from DOT file.")
            else:
                st.error("DOT file not found.")

        # Find Rate Determining Step (RDS)
        if st.button("Find RDS"):
            if os.path.exists(DOT_FILE_PATH):
                intermediates, reactants, products = parse_dot_file(DOT_FILE_PATH)
                graph = extract_reactions(DOT_FILE_PATH)
                st.header("Reactant-Product Pairs and their RDS")

                for reactant in reactants:
                    for product in products:
                        path, rds = find_rds(graph, reactant, product)
                        if path:
                            st.subheader(f"Reactant: {reactant}, Product: {product}")
                            st.write(f"Path: {' -> '.join(path)}")
                            if rds:
                                st.write(f"RDS: {rds[0]} -> {rds[1]}")
                                rate = next(rate for n, rate in graph[rds[0]] if n == rds[1])
                                if rate == 0:
                                    st.info("RDS: No RDS (rate = 0)")
                                else:
                                    st.write(f"Rate: {rate:.3e}")
                            else:
                                st.warning("No RDS (all rates are zero)")
                        else:
                            st.warning(f"No path from {reactant} to {product}")
                        st.markdown("---")
            else:
                st.error("Network file not found.")

        # Download run folder
        if os.path.exists(RESULT_FOLDER):
            zip_folder(RESULT_FOLDER, ZIP_OUTPUT_PATH)
            with open(ZIP_OUTPUT_PATH, "rb") as zip_file:
                st.download_button(
                    label="Download Simulation Results (run/)",
                    data=zip_file,
                    file_name="simulation_results.zip",
                    mime="application/zip"
                )
        else:
            st.warning(f"The folder '{RESULT_FOLDER}' does not exist.")

    except Exception as e:
        st.error(f"Error loading or reading MKM file: {e}")

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=folder_path)
                zipf.write(full_path, arcname)        


def main():
    mkm_file_solver()


if __name__ == "__main__":
    main()
