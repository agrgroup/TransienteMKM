import streamlit as st
import os
import shutil

# Function to execute the command
def run_mkmcxx(input_file):
    # Assuming the directory is already set up to hold the results.
    # Construct the command with the file name from the uploaded file
    # input_file = os.path.join('..', 'bin', 'mkmcxx')
    # os.system(f"{input_file} -i .\\input_file.mkm")

    import subprocess
    st.write(os.getcwd())
   # executable_path = os.path.join(os.getcwd(), 'bin', 'mkmcxx')
    executable_path = r"D:\mkmcxx\mkmcxx-2.15.3-windows-x64\mkmcxx_2.15.3\bin\mkmcxx.exe"
    result = subprocess.run([executable_path, '-i', '.\\input_file.mkm'], capture_output=True)
    if result.returncode == 0:
        print("Command executed successfully!")
        print(result.stdout.decode())
    else:
        print("Error running command:")
        print(result.stderr.decode())



# Streamlit UI
st.title("MKMCXX Execution")

# Upload file input
uploaded_file = st.file_uploader("Upload your input.mkm file", type="mkm")

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    input_path = os.path.join("temp", uploaded_file.name)
    os.makedirs(os.path.dirname(input_path), exist_ok=True)

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.write("File uploaded successfully!")

    # Execute the command using the uploaded file
    if st.button("Run MKMcxx"):
        # Run the command
        run_mkmcxx(input_path)
        
        # Display the results directory
        result_dir = "run"
        if os.path.exists(result_dir):
            st.write(f"Results directory created at: {os.path.abspath(result_dir)}")
            # Optionally list files in the results directory
            files = os.listdir(result_dir)
            st.write("Files in results directory:")
            st.write(files)
        else:
            st.write("No results directory found.")
