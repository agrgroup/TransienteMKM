import streamlit as st
import os
from utility import *  # Assuming you have functions for handling MKM files
import pandas as pd
import sys
import shutil
from openpyxl import load_workbook
from io import BytesIO
import numpy as np
import networkx as nx  # Assuming you are using NetworkX for graph visualization

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)
from inp_file_multiple import *
from graph_helper import *
from utility import *

st.set_page_config(
    page_title="MKM Input File Generator and Solver",
    page_icon="👋",
    initial_sidebar_state="expanded"
)

# Title of the Streamlit app
st.title('e-MKM Solver')

# Define the second page functionality to handle .mkm file
def mkm_file_solver():
    st.header("MKM File Solver")

    # Upload MKM Input File
    uploaded_mkm_file = st.file_uploader("Upload MKM Input File", type="mkm")

    if uploaded_mkm_file:
        try:
            # Read the MKM file (you can add a function to parse this file if necessary)
            mkm_data = uploaded_mkm_file.read().decode("utf-8")
            st.write("MKM Input File Loaded Successfully!")

            # Display a preview of the content (assuming the file contains readable data)
            st.text_area("Preview of MKM Input File", mkm_data, height=300)

            # Store the uploaded MKM file in a temporary location
            temp_file_path = os.path.join(uploaded_mkm_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_mkm_file.getbuffer())

            # Run Solver Button
            if st.button("Run MKM Solver"):
                result_message, success = run_executable(temp_file_path)  # Use the temp path here
                if success:
                    st.success(result_message)
                    coverage()  # Assuming coverage() is a function to display coverage results
                else:
                    st.error(result_message)

            dot_file_path = "run/networkplots/network_01_0298K.dot"
        
            if st.button("Create Reaction Network Visualization"):
                if os.path.exists(dot_file_path):
                    graph = create_reaction_network_visualization(dot_file=dot_file_path)
                    if graph:
                        graph_svg = graph.pipe(format='svg').decode('utf-8')
                        st.image(graph_svg)
                        
                        # Download Button for High-Quality Reaction Network
                        st.download_button(
                            label="Download Reaction Network (SVG)",
                            data=graph.pipe(format='svg'),
                            file_name="reaction_network.svg",
                            mime="image/svg+xml"
                        )
                    else:
                        st.error("Failed to create the graph. Please check the DOT file content.")
                else:
                    st.error("The specified file does not exist. Please check the file path.")         
            
            # Existing functionality for RDS (No changes here)
            if st.button("Find RDS"):
                if os.path.exists(dot_file_path):  
                    intermediates, reactants, products = parse_dot_file(dot_file_path)
                    graph = extract_reactions(dot_file_path)
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
                                        st.write("RDS: No RDS")
                                    else:
                                        st.write(f"Rate: {rate:.3e}") 
                                else:     
                                    st.write("No RDS (all rates are zero)")
                            else:
                                st.write(f"No path from {reactant} to {product}") 
                            st.write("---")  # Add a separator between each pair           
            else:
                st.error("Network file not found")   

            folder_to_download = "run/"
            zip_output_path = "single_run_run.zip"     
            if os.path.exists(folder_to_download):

                # Compress the folder into a .zip file
                zip_folder(folder_to_download, zip_output_path)  
                with open(zip_output_path, "rb") as zip_file:
                    btn = st.download_button(
                        label="Download Simulation Results (run/)",
                        data=zip_file,
                        file_name="simulation_results.zip",
                        mime="application/zip"
                    )

            else:
                st.warning(f"The folder '{folder_to_download}' does not exist.")                 


        except Exception as e:
            st.error(f"Error loading or reading MKM file: {str(e)}")

# Main function to select between pages
def main():
    mkm_file_solver()  

if __name__ == "__main__":
    main()
