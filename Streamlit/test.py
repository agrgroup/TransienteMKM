import streamlit as st
import pandas as pd
import xlwings as xw

def read_formulas(file_name, sheet_name, column_name):
    """
    Recalculates the formulas in an Excel file, saves the file, and returns the dataframe with the updated values.
    
    Args:
    file_name (str): Path to the Excel file.
    sheet_name (str): Name of the sheet to process.
    column_name (str): The column name to focus on in the resulting DataFrame.
    
    Returns:
    pd.DataFrame: DataFrame with the computed values from the specified column.
    """
    try:
        # Open Excel file
        app = xw.App(visible=False)  # Open Excel in the background
        wb = xw.Book(file_name)
        sheet = wb.sheets[sheet_name]

        # Recalculate all formulas in the workbook
        wb.app.calculation = 'automatic'
        wb.save(file_name)  # Save the file after recalculation
        wb.close()
        app.quit()

        # Read the recalculated file with pandas
        df = pd.read_excel(file_name, engine="openpyxl", sheet_name=sheet_name)
        
        # Optionally, focus on the specified column if needed
        if column_name in df.columns:
            return df[[column_name]]  # Return only the specified column
        else:
            raise ValueError(f"Column '{column_name}' not found in the sheet.")
    
    except Exception as e:
        print(f"Error: {e}")
        return None

# Streamlit App
st.title("Excel Formula Recalculation")

# File uploader to upload the Excel file
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

# Sheet name input
sheet_name = st.text_input("Enter the Sheet Name", value="Sheet1")

# Column name input
column_name = st.text_input("Enter the Column Name to extract", value="A")

if uploaded_file:
    try:
        # Save the uploaded file temporarily
        with open("temp_file.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Get the recalculated values from the specified column
        df = read_formulas("temp_file.xlsx", sheet_name, column_name)
        
        if df is not None:
            st.write(f"**Updated Values in '{column_name}' column:**")
            st.dataframe(df)
        else:
            st.error("Failed to extract data.")
    
    except Exception as e:
        st.error(f"Error: {e}")
