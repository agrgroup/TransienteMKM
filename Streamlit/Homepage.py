import streamlit as st
import pandas as pd
import os
from utility import *
from graph_helper import *
import zipfile
import shutil


st.set_page_config(
    page_title="MKM Input File Generator and Solver",
    page_icon="👋",
)

# Title of the Streamlit app
st.title('e-MKM Input File Generator and Solver')


def zip_folder(folder_path, output_zip_path):
    """Compress a folder into a zip file."""
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                zipf.write(file_path, arcname)


def main():
    if "uploaded_file" not in st.session_state:
        st.session_state["uploaded_file"] = ""

    # Upload Excel file
    uploaded_file = st.file_uploader("Upload Excel File", type="xlsx")
    
    if uploaded_file:
        try:
            data = pd.read_excel(uploaded_file)
            st.write("Data Loaded Successfully!")
        except Exception as e:
            st.error(f"Error Loading Data: {str(e)}")
            return
        try:
            data1 = pd.read_excel(uploaded_file, sheet_name="Reactions")
            st.write("Reactions Loaded Successfully!")
            df1 = data1
            st.write("Reactions Preview:", df1.head())
        except Exception as e:
            st.error(f"Error reading Reactions sheet: {str(e)}")
            return
        
        try:
            data2 = pd.read_excel(uploaded_file, sheet_name="Local Environment")
            st.write("Local Environment Loaded Successfully!")
            df2 = data2
            st.write("Local Environment Preview:", df2.head())
        except Exception as e:
            st.error(f"Error reading Local Environment sheet: {str(e)}")
            return
        
        try:
            data3 = pd.read_excel(uploaded_file, sheet_name="Input-Output Species")
            st.write("Input-output Loaded Successfully!")
            df3 = data3
            st.write("Input-output Preview:", df3.head())
        except Exception as e:
            st.error(f"Error reading Input-output sheet: {str(e)}")
            return
        
        # Generate Input File Button
        if st.button("Generate MKM Input"):
            try:
                # Call the function to generate the input file
                input_file_path = inp_file_gen(uploaded_file)
                st.success("Input file generated successfully!")

                # After generating the file, allow the user to download it
                with open(input_file_path, "rb") as file:
                    st.download_button(
                        label="Download Generated MKM Input ",
                        data=file,
                        file_name="input_file.mkm",
                        mime="application/octet-stream"
                    )
            except Exception as e:
                st.error(f"Error generating input file: {str(e)}")

        input_file_path = "single_run/input_file.mkm"
        # Run Solver Button
        if st.button("Run Solver"):
        
            result_message, success = run_executable(input_file_path)
            if success:
                st.success(result_message)
                coverage()
            else:
                st.error(result_message)
        dot_file_path = "run/networkplots/network_01_0298K.dot"
        
        if st.button("Create Reaction Network Visualization"):
            if os.path.exists(dot_file_path):
                graph = create_reaction_network_visualization(dot_file=dot_file_path)
                if graph:
                    graph_svg = graph.pipe(format='svg').decode('utf-8')
                    st.image(graph_svg)
                else:
                        st.error("Failed to create the graph. Please check the DOT file content.")
            else:
                   st.error("The specified file does not exist. Please check the file path.")         




        if st.button("Find RDS"):
            if os.path.exists(dot_file_path):  
                intermediates, reactants, products = parse_dot_file(dot_file_path)
                graph = extract_reactions(dot_file_path)
                st.header("Reactant-Product Pairs and their RDS")

                for reactant in reactants:
                    for product in products:
                        path, rds = find_rds(graph, reactant, product)
                        if path:
                            st.subheader(f"Reactant: {reactant},Product: {product}")
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


                # Download Folder Button
        folder_to_download = "run/"
        zip_output_path = "single_run_run.zip" 

        if os.path.exists(folder_to_download):
            # Compress the folder into a .zip file
            zip_folder(folder_to_download, zip_output_path)  

         # Provide a download button for the .zip file
            with open(zip_output_path, "rb") as zip_file:
                btn = st.download_button(
                    label="Download Simulation Results (run/)",
                    data=zip_file,
                    file_name="simulation_results.zip",
                    mime="application/zip"
                )
        else:
            st.warning(f"The folder '{folder_to_download}' does not exist.")         

        
                       

if __name__ == "__main__":
    main()
