import streamlit as st
import pandas as pd
import os
import subprocess
import numpy as np
import networkx as nx
import zipfile
from graph_helper import create_reaction_network_visualization, parse_dot_file, extract_reactions, find_rds
from utility import * 
from inp_file_gen import inp_file_gen
from mkm_parameters import *
import zipfile

DOT_FILE_PATH = "run/networkplots/network_01_0298K.dot"
RESULT_FOLDER = "run/"
ZIP_OUTPUT_PATH = "single_run_run.zip"


st.set_page_config(
    page_title="MKM Input File Generator and Solver",
    page_icon="👋",
)

st.title('MKM Input File Generator and Solver')

# Function to run the mkmcxx solver
def run_executable(input_file):
    executable_path = os.path.join(os.path.dirname(__file__), 'bin', 'mkmcxx.exe')
    st.write(f"Using Executable: {executable_path}")

    if os.path.exists(executable_path):
        try:
            result = subprocess.run([executable_path, '-i', input_file],
                                    capture_output=True, text=True)
            st.write("Solver Output (stdout):")
            st.text(result.stdout)
            if result.stderr:
                st.write("Solver Error Output (stderr):")
                st.text(result.stderr)
            return ("Solver ran successfully!" if result.returncode == 0 else f"Error running solver: {result.stderr}", result.returncode == 0)
        except Exception as e:
            return (f"Execution error: {str(e)}", False)
    else:
        return (f"Executable not found: {executable_path}", False)

# Parse coverage.dat
def get_coverage_values(cov_path):
    with open(cov_path) as file:
        lines = file.readlines()
    adsorbate_keys = lines[0].strip().split()
    data = {key: [] for key in adsorbate_keys}
    for line in lines[1:]:
        values = list(map(float, line.strip().split()))
        for i, key in enumerate(adsorbate_keys):
            data[key].append(values[i])
    return data

def show_coverage():
    path = "run/range/coverage.dat"
    if os.path.exists(path):
        covs = get_coverage_values(path)
        relevant = {k: v for k, v in covs.items() if '*' in k}
        df = pd.DataFrame(relevant).T.reset_index()
        df.columns = ['Adsorbates', 'Coverage']
        st.write("Coverage Data:")
        st.dataframe(df)
    else:
        st.error("coverage.dat file not found.")

# Main app logic
def main():
    uploaded_file = st.file_uploader("Upload Excel File", type="xlsx")
    if uploaded_file:
        try:
            df_rxn = pd.read_excel(uploaded_file, sheet_name="Reactions")
            df_env = pd.read_excel(uploaded_file, sheet_name="Local Environment")
            df_io = pd.read_excel(uploaded_file, sheet_name="Input-Output Species")
        except Exception as e:
            st.error(f"Failed to read sheets: {e}")
            return

        required_rxn_cols = {"Reactions", "G_f", "G_b"}
        required_env_cols = {"pH", "V", "Pressure"}
        required_io_cols = {"Species", "Concentration"}

        if not required_rxn_cols.issubset(df_rxn.columns):
            st.error("Missing required columns in 'Reactions' sheet.")
            return
        if not required_env_cols.issubset(df_env.columns):
            st.error("Missing required columns in 'Local Environment' sheet.")
            return
        if not required_io_cols.issubset(df_io.columns):
            st.error("Missing required columns in 'Input-Output Species' sheet.")
            return

        st.success("Excel data loaded successfully.")

        # Display data
        st.subheader("Reactions Preview")
        st.dataframe(df_rxn.head())
        st.subheader("Local Environment Preview")
        st.dataframe(df_env.head())
        st.subheader("Input-Output Species Preview")
        st.dataframe(df_io.head())

        # Extract values
        pH_list = df_env["pH"].tolist()
        V_list = df_env["V"].tolist()
        P = df_env["Pressure"].iloc[0]
        gases = df_io["Species"].tolist()
        concentrations = df_io["Concentration"].tolist()
        rxn = df_rxn["Reactions"]
        Ea = df_rxn["G_f"]
        Eb = df_rxn["G_b"]
        Temp = df_env.get("Temperature", pd.Series([298])).iloc[0]
        Time = df_env.get("Time", pd.Series([1e3])).iloc[0]
        Abstol = df_env.get("Abstol", pd.Series([1e-12])).iloc[0]
        Reltol = df_env.get("Reltol", pd.Series([1e-6])).iloc[0]

        # Parse reactions
        Reactant1, Reactant2, Reactant3 = [], [], []
        Product1, Product2, Product3 = [], [], []
        adsorbates = set()

        for r in rxn:
            lhs, rhs = map(str.strip, r.split("→"))
            reactants = [f"{{{x.strip()}}}" for x in lhs.split("+")]
            products = [f"{{{x.strip()}}}" for x in rhs.split("+")]
            reactants += [""] * (3 - len(reactants))
            products += [""] * (3 - len(products))
            Reactant1.append(reactants[0])
            Reactant2.append(reactants[1])
            Reactant3.append(reactants[2])
            Product1.append(products[0])
            Product2.append(products[1])
            Product3.append(products[2])
            for item in reactants + products:
                clean = item.strip("{}")
                if "*" in clean and clean != "*":
                    adsorbates.add(clean)

        adsorbates = list(adsorbates)
        activity = np.zeros(len(adsorbates))

        # Generate input file
        try:
            inp_file_gen(rxn, pH_list, V_list, gases, concentrations, adsorbates, activity,
                         Reactant1, Reactant2, Reactant3, Product1, Product2, Product3,
                         Ea, Eb, P, Temp, Time, Abstol, Reltol)
            st.success("Input file generated.")
        except Exception as e:
            st.error(f"Failed to generate input file: {e}")
            return

        # Run solver
        input_file_path = 'input_file.mkm'
        if st.button("Run Solver"):
            result_message, success = run_executable(input_file_path)
            (st.success if success else st.error)(result_message)
            if success:
                show_coverage()

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

        # Download simulation results
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
    

if __name__ == "__main__":
    main()
