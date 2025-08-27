"""
Data extraction and manipulation module for microkinetic modeling.
Fixed all indentation errors, HTML entities, and added proper error handling.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from openpyxl import load_workbook
import xlwings as xw
import math


logger = logging.getLogger(__name__)

class ExcelDataProcessor:
    """Handles Excel file operations for microkinetic modeling."""

    def __init__(self, excel_path: str):
        """Initialize with path to Excel file."""
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

    def modify_local_environment(self, pH: float, V: float, output_path: str = None) -> str:
        """
        Modify pH and V values in the Local Environment sheet.

        Args:
            pH: New pH value
            V: New potential value
            output_path: Path for modified file (default: input_data.xlsx)

        Returns:
            Path to modified file
        """
        if output_path is None:
            output_path = "input_data.xlsx"

        try:
            # Fixed the hardcoded path issue from original code
            workbook = load_workbook(filename=str(self.excel_path))
            sheet = workbook['Local Environment']

            # Update pH values
            self._update_column_values(sheet, 'pH', pH)

            # Update V values  
            self._update_column_values(sheet, 'V', V)

            workbook.save(filename=output_path)
            #logger.info(f"Modified Excel file saved to: {output_path}")
            logger.info(f"Excel modified successfully: pH={pH}, V={V}V → {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error modifying Excel file: {e}")
            raise

    def _update_column_values(self, sheet, column_name: str, new_value: float) -> None:
        """Update all values in a specific column."""
        column_index = None

        # Find column index
        for cell in sheet[1]:
            if cell.value == column_name:
                column_index = cell.column
                break

        if column_index is None:
            logger.warning(f"Column '{column_name}' not found")
            return

        # Update all non-None values in the column
        for row in range(2, sheet.max_row + 1):
            current_value = sheet.cell(row=row, column=column_index).value
            if current_value is not None:
                sheet.cell(row=row, column=column_index).value = new_value

    def read_column_data(self, sheet_name: str, column_name: str) -> List[Any]:
        """
        Read all values from a specific column using xlwings.

        Args:
            sheet_name: Name of the Excel sheet
            column_name: Name of the column

        Returns:
            List of values from the column
        """
        try:
            with xw.Book(str(self.excel_path)) as wb:
                sheet = wb.sheets[sheet_name]
                header_row = sheet.range('1:1').value

                if column_name not in header_row:
                    logger.warning(f"Column '{column_name}' not found in sheet '{sheet_name}'")
                    return []

                column_index = header_row.index(column_name) + 1
                column_values = sheet.range((2, column_index), 
                                          (sheet.cells.last_cell.row, column_index)).value

                # Filter out None values and convert single values to list
                if not isinstance(column_values, list):
                    column_values = [column_values] if column_values is not None else []

                return [value for value in column_values if value is not None]

        except Exception as e:
            logger.error(f"Error reading column data: {e}")
            return []

    def extract_all_data(self, modified_excel_path: str) -> Dict[str, Any]:
        """
        Extract all necessary data from Excel file.

        Args:
            modified_excel_path: Path to the modified Excel file

        Returns:
            Dictionary containing all extracted data
        """
        try:
            # Read data using pandas for reliability
            df_reactions = pd.read_excel(modified_excel_path, sheet_name='Reactions')
            df_local_env = pd.read_excel(modified_excel_path, sheet_name='Local Environment')
            df_species = pd.read_excel(modified_excel_path, sheet_name='Input-Output Species')

            # Extract reaction data
            reactions = df_reactions['Reactions'].tolist()
            Ea = self.read_column_data('Reactions', 'G_f') or df_reactions['G_f'].tolist()
            Eb = self.read_column_data('Reactions', 'G_b') or df_reactions['G_b'].tolist()
            delE_list = self.read_column_data('Reactions', 'DelG_rxn') or df_reactions['DelG_rxn'].tolist()

            delE_index = 0
            for i in range(len(Ea)):
                # Handle None/NaN by treating them as 0 for comparison
                ea_val = Ea[i] if Ea[i] is not None and not math.isnan(Ea[i]) else 0
                eb_val = Eb[i] if Eb[i] is not None and not math.isnan(Eb[i]) else 0

                if ea_val == 0 and eb_val == 0:
                    if delE_index < len(delE_list):  # Avoid IndexError
                        delE = delE_list[delE_index]
                        
                        # Only proceed if delE is a valid number
                        if delE is not None and not math.isnan(delE):
                            if delE > 0:
                                Ea[i] = delE
                            else:
                                Eb[i] = -delE

                        delE_index += 1
                    else:
                        # Optional: warn if we ran out of delE values
                        print(f"Warning: No delE value for index {i}")

            # Extract environment data
            V = df_local_env['V'].iloc[0]
            pH = df_local_env['pH'].iloc[0] 
            P = df_local_env['Pressure'].iloc[0]

            # Extract species data
            gases = df_species['Species'].tolist()
            concentrations = (self.read_column_data('Input-Output Species', 'Input MKMCXX') or 
                            df_species.get('Input MKMCXX', []).tolist())

            # Parse reactions
            parsed_reactions = self._parse_reactions(reactions)

            # Find adsorbates
            adsorbates = self._extract_adsorbates(parsed_reactions)

            return {
                'reactions': reactions,
                'Ea': Ea,
                'Eb': Eb,
                'V': V,
                'pH': pH,
                'P': P,
                'gases': gases,
                'concentrations': concentrations,
                'adsorbates': adsorbates,
                'activity': np.zeros(len(adsorbates)),
                **parsed_reactions
            }

        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            raise

    def _parse_reactions(self, reactions: List[str]) -> Dict[str, List[str]]:
        """Parse reaction strings into reactants and products."""
        reactant1, reactant2, reactant3 = [], [], []
        product1, product2, product3 = [], [], []

        for rxn in reactions:
            try:
                # Split reaction into reactants and products
                reactants_str, products_str = rxn.strip().split("→")

                # Parse reactants
                reactants = [r.strip() for r in reactants_str.split("+")]
                reactant1.append(f"{{{reactants[0]}}}")
                reactant2.append(f"{{{reactants[1]}}}" if len(reactants) > 1 else "")
                reactant3.append(f"{{{reactants[2]}}}" if len(reactants) > 2 else "")

                # Parse products
                products = [p.strip() for p in products_str.split("+")]
                product1.append(f"{{{products[0]}}}")
                product2.append(f"{{{products[1]}}}" if len(products) > 1 else "")
                product3.append(f"{{{products[2]}}}" if len(products) > 2 else "")

            except Exception as e:
                logger.error(f"Error parsing reaction '{rxn}': {e}")
                # Add empty entries to maintain list consistency
                for lst in [reactant1, reactant2, reactant3, product1, product2, product3]:
                    lst.append("")

        return {
            'Reactant1': reactant1,
            'Reactant2': reactant2,
            'Reactant3': reactant3,
            'Product1': product1,
            'Product2': product2,
            'Product3': product3
        }

    def _extract_adsorbates(self, parsed_reactions: Dict[str, List[str]]) -> List[str]:
        """Extract unique adsorbates from parsed reactions."""
        adsorbates = set()

        # Check all reactants and products for adsorbates (containing *)
        for key in ['Reactant1', 'Reactant2', 'Product1', 'Product2']:
            for item in parsed_reactions.get(key, []):
                if "*" in item and item != "":
                    species = item.strip("{}").strip()
                    if species != "*":
                        adsorbates.add(species)

        return list(adsorbates)

def data_extract(pH: float, V: float, inp_path: str) -> Tuple:
    """
    Main data extraction function (maintains compatibility with original interface).
    Fixed all bugs from the original version.

    Returns:
        Tuple containing all extracted data in original order
    """
    processor = ExcelDataProcessor(inp_path)

    # Modify Excel file with new pH and V values
    modified_path = processor.modify_local_environment(pH, V)

    # Extract all data
    data = processor.extract_all_data(modified_path)

    return (
        data['gases'],
        data['concentrations'], 
        data['adsorbates'],
        data['activity'],
        data['Reactant1'],
        data['Reactant2'],
        data['Reactant3'],
        data['Product1'],
        data['Product2'],
        data['Product3'],
        data['Ea'],
        data['Eb'],
        data['P'],
        data['reactions']
    )
