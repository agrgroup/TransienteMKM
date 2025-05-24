import streamlit as st
import pandas as pd
import os
import subprocess

from dependencies import *
#from data_extract import *
#from solver_settings import *
from inp_file_gen import *
from mkm_parameters import *
#from path import *
import shutil
from io import StringIO

st.set_page_config(
    page_title="Multipage App",
    page_icon="👋",
)

st.title("Main Page")
st.sidebar.success("Select a page above.")


# Function to run the executable and generate the required outputs
def run_executable(input_file):
    #executable_path = os.path.join(os.getcwd(),'/bin/mkmcxx')    
    executable_path = r"D:\mkmcxx\mkmcxx-2.15.3-windows-x64\mkmcxx_2.15.3\bin\mkmcxx.exe"
    st.write(executable_path)
    if os.path.exists(executable_path):
        st.write(f"Executable found at: {executable_path}")
        try:
            # Run the executable with the input file using subprocess
            result = subprocess.run([executable_path, '-i', input_file],
                                    capture_output=True, text=True)
            
            # Print the stdout (standard output) and stderr (standard error)
            st.write("Solver Output (stdout):")
            st.text(result.stdout)  # This will show the standard output in Streamlit

            if result.stderr:
                st.write("Solver Error Output (stderr):")
                st.text(result.stderr)  # This will show the error output (if any)
            
            # Check for success or failure
            if result.returncode == 0:
                return "Solver ran successfully!", True
            else:
                return f"Error running solver: {result.stderr}", False
        except Exception as e:
            return f"Error executing command: {str(e)}", False
    else:
        return "Executable not found at the given path.", False
def get_val (cov_path):   
    cov_file = open(cov_path)
    
    cov_val = []
    
    cov_lines = cov_file.readlines()
    
    adsorbate_keys = cov_lines[0].strip().split()
    
    cov_dat_dict = {}
    
    for key in adsorbate_keys:
        cov_dat_dict[key] = []
    
    for line in cov_lines[1:]:
        vals = line.strip().split()
        vals = list(map(lambda x : float(x), vals))
        c=0
        for key in adsorbate_keys:
            cov_dat_dict[key].append(vals[c])
            c+=1
            
    cov_file.close()
    return cov_dat_dict
    
def coverage():
    coverage_file_path = "run/range/coverage.dat"
    
    if os.path.exists(coverage_file_path):
        covs = get_val(coverage_file_path)
        covs_relevant ={}

        for key in covs.keys():
            if '*' in key:
                covs_relevant[key] = covs[key]
        #Read the data from the coverage.dat file
        # list coverrage dictionary
        covs_relevant_df = pd.DataFrame(covs_relevant)
        covs_relevant_df = covs_relevant_df.T
        covs_relevant_df = covs_relevant_df.reset_index()
        covs_relevant_df.columns = ['Adsorbates', 'Coverage']
        st.write("Coverage Data:")
        st.write(covs_relevant_df)
    else:
        st.error("coverage.dat file not found in the expected directory.")    


def main():
    # Title of the Streamlit app
    st.title('MKM Input File Generator and Solver')

    # Upload Excel file
    uploaded_file = st.file_uploader("Upload Excel File", type="xlsx")
    
    if uploaded_file:
        # Read the uploaded Excel file into a pandas DataFrame
        try:
            data1 = pd.read_excel(uploaded_file, sheet_name="Reactions")
            st.write("Reactions Loaded Successfully!")
            # Show sheet names and allow the user to select one
            #st.write("Available Sheets:", list(data1.keys()))
            #selected_sheet = st.selectbox("Select a Sheet", list(data1.keys()),key="sheet1")
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
            st.write("input-output Loaded Successfully!")
            df3 = data3
            st.write("input-output Preview:", df3.head())
        except Exception as e:
            st.error(f"Error reading input-output sheet: {str(e)}")
            return

        # Extract necessary data from the dataframe for your solver
        try:
            # You can customize the column names based on how your Excel is structured
            global pH_list, V_list, gases,rxn, concentrations,Ea, Eb, P
            pH_list = df2["pH"].tolist()
            V_list = df2["V"].tolist()
            gases = df3["Species"].tolist()
            concentrations = df3["Concentration"].tolist()
            rxn=df1["Reactions"]
            Ea=df1["G_f"]
            Eb=df1["G_b"]
            V=df2["V"][0]
            pH=df2["pH"][0]
            P=df2["Pressure"][0]
            concentrations=df3["Concentration"].to_list()
            st.write("Parameters extracted successfully!")

             # Display the extracted parameters
            # st.write("Extracted Parameters:")
            # st.write(f"pH List: {pH_list}")
            # st.write(f"Voltage List: {V_list}")
            # st.write(f"Gases: {gases}")
            # st.write(f"Concentrations: {concentrations}")
            # st.write(f"Pressure: {P}")

            # st.write(f"Reactions: {rxn}")


        except Exception as e:
            st.error(f"Error extracting parameters: {str(e)}")
            return
        
                # Extract necessary data from the dataframe for your solver
              
        try:
            # You can customize the column names based on how your Excel is structured
            global  adsorbates, activity, Reactant1, Reactant2, Reactant3, Product1, Product2, Product3, Time, Temp, Abstol, Reltol
            Reactant1=[]
            Reactant2=[]
            Reactant3=[]
            Product1=[]
            Product2=[]
            Product3=[]
            adsorbates=[]  

            for i in range(len(rxn)):
                Reactant1.append("{"+rxn[i].strip().split("→")[0].split("+")[0].strip()+"}")
                if(len(rxn[i].strip().split("→")[0].split("+"))==3):
                    Reactant2.append("{"+rxn[i].strip().split("→")[0].split("+")[1].strip()+"}")
                    Reactant3.append("{"+rxn[i].strip().split("→")[0].split("+")[2].strip()+"}")

                elif (len(rxn[i].strip().split("→")[0].split("+"))==2):
                    Reactant2.append("{"+rxn[i].strip().split("→")[0].split("+")[1].strip()+"}")
                    Reactant3.append("")
                else:
                    Reactant2.append("")
                    Reactant3.append("")    

                Product1.append("{"+rxn[i].strip().split("→")[1].split("+")[0].strip()+"}")
                if(len(rxn[i].strip().split("→")[1].split("+"))==3):
                    Product2.append("{"+rxn[i].strip().split("→")[1].split("+")[1].strip()+"}")
                    Product3.append("{"+rxn[i].strip().split("→")[1].split("+")[2].strip()+"}")
                elif(len(rxn[i].strip().split("→")[1].split("+"))==2):
                    Product2.append("{"+rxn[i].strip().split("→")[1].split("+")[1].strip()+"}")
                    Product3.append("")  
                else:
                    Product2.append("")
                    Product3.append("")

            for index in Reactant1:
                if "*" in index and index.strip("{").strip("}") not in adsorbates:
                    adsorbates.append(index.strip("{").strip("}"))

            for index in Reactant2:
                if "*" in index and index.strip("{").strip("}") not in adsorbates:
                    adsorbates.append(index.strip("{").strip("}"))

            for index in Product1:
                if "*" in index and index.strip("{").strip("}") not in adsorbates:
                    adsorbates.append(index.strip("{").strip("}"))

            for index in Product2:
                if "*" in index and index.strip("{").strip("}") not in adsorbates:
                    adsorbates.append(index.strip("{").strip("}"))       

            adsorbates.remove("*")
            activity=np.zeros(len(adsorbates))

            st.write("Intermediates extracted successfully!")

            # Display the extracted intermediates
            # st.write("Extracted intermediates:")
            # st.write(f"Reactant 1: {Reactant1}")
            # st.write(f"Reactant 2: {Reactant2}")
            # st.write(f"Reactant 3: {Reactant3}")
            # st.write(f"Product 1: {Product1}")
            # st.write(f"Product 2: {Product2}")
            # st.write(f"Product 3: {Product3}")
            # st.write(f"Adsorbates: {adsorbates}")

            # st.write(f"Voltage List: {V_list}")
            # st.write(f"Gases: {gases}")
            # st.write(f"Concentrations: {concentrations}")
            # st.write(f"Pressure: {P}")

        except Exception as e:
            st.error(f"Error extracting Intermediates: {str(e)}")
            return
        
        # Run the input file generation and solver (based on your existing code)
        try:
            # Make the directories and run the input file generator and solver
            inp_file_gen(rxn,pH_list, V_list, gases, concentrations, adsorbates, activity, Reactant1, Reactant2, Reactant3, Product1, Product2, Product3, Ea, Eb, P, Temp, Time, Abstol, Reltol)
            #st.success("Solver executed successfully!")
            st.write("Input file generated successfully!")
            

        except Exception as e:
            st.error(f"Error running generating input file: {str(e)}")

        input_file_path = 'input_file.mkm'  # You would generate the input file here
        if st.button("Run Solver"):
                    result_message, success = run_executable(input_file_path)
                    if success:
                        st.success(result_message)
                        coverage() 
                    else:
                        st.error(result_message)

                       



if __name__ == "__main__":
    main()
