"""
Plotting module for microkinetic modeling results visualization.
Fixed all HTML entities, indentation errors, and improved functionality.
"""

import os
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
import pandas as pd
import numpy as np
from matplotlib import rc, rcParams

logger = logging.getLogger(__name__)

class CoveragePlotter:
    """Handles plotting of coverage data from microkinetic simulations."""

    def __init__(self, base_directory: str = None):
        """
        Initialize plotter with base directory.

        Args:
            base_directory: Base directory containing simulation results
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self._setup_plotting_style()

    def _setup_plotting_style(self) -> None:
        """Set up matplotlib plotting style."""
        rc('axes', linewidth=2)
        plt.rcParams.update({
            'font.size': 12,
            'font.weight': 'bold',
            'axes.labelweight': 'bold',
            'axes.titleweight': 'bold'
        })

    def read_coverage_data(self, pH: float, V: float) -> Dict[str, List[float]]:
        """
        Read coverage data from simulation results.
        Fixed path handling issues from original code.

        Args:
            pH: pH value
            V: Potential value

        Returns:
            Dictionary with species as keys and coverage lists as values
        """
        try:
            # Construct path to coverage data
            data_path = self.base_directory / f"pH_{pH}" / f"V_{V}"

            # Find run directory
            run_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name.startswith("run")]
            if not run_dirs:
                logger.warning(f"No run directory found in {data_path}")
                return {}

            run_dir = run_dirs[0]  # Take first run directory
            coverage_file = run_dir / "range" / "coverage.dat"

            if not coverage_file.exists():
                logger.warning(f"Coverage file not found: {coverage_file}")
                return {}

            # Read coverage data
            with open(coverage_file, 'r') as f:
                lines = f.readlines()

            if not lines:
                return {}

            # Parse header
            headers = lines[0].strip().split()
            coverage_data = {header: [] for header in headers}

            # Parse data lines
            # Parse data lines with negative value handling
            for line in lines[1:]:
                if line.strip():
                    values = list(map(float, line.strip().split()))
                    for i, header in enumerate(headers):
                        if i < len(values):
                            # Set negative coverage values to zero
                            coverage_value = max(0.0, values[i])
                            coverage_data[header].append(coverage_value)
                            if values[i] < 0:
                                logger.debug(f"Negative coverage found for {header}: {values[i]} -> set to 0.0")

            return coverage_data

        except Exception as e:
            logger.error(f"Error reading coverage data for pH={pH}, V={V}: {e}")
            return {}

    def get_final_coverages(self, pH_list: List[float], V_list: List[float]) -> Dict[float, Dict[float, Dict[str, float]]]:
        """
        Get final coverage values for all pH and V combinations.

        Args:
            pH_list: List of pH values
            V_list: List of potential values

        Returns:
            Nested dictionary: {pH: {V: {species: final_coverage}}}
        """
        all_coverages = {}

        for pH in pH_list:
            all_coverages[pH] = {}

            for V in V_list:
                coverage_data = self.read_coverage_data(pH, V)
                final_coverages = {}

                # Get final coverage for each species
                # Get final coverage for each species
                for species, values in coverage_data.items():
                    if values and '*' in species:  # Only adsorbates
                        # Ensure final coverage is non-negative
                        final_coverage = max(0.0, values[-1])
                        final_coverages[species] = final_coverage


                all_coverages[pH][V] = final_coverages

        return all_coverages

    def plot_coverage_vs_potential(self, pH_list: List[float], V_list: List[float], 
                                 save_plots: bool = True, show_plots: bool = True,
                                 output_dir: str = "plots") -> None:
        """
        Plot coverage vs potential for each pH.
        Fixed HTML entities and improved plotting logic.

        Args:
            pH_list: List of pH values to plot
            V_list: List of potential values
            save_plots: Whether to save plots
            show_plots: Whether to display plots
            output_dir: Directory to save plots
        """
        if save_plots:
            plots_dir = Path(output_dir)
            plots_dir.mkdir(exist_ok=True)

        # Get all coverage data
        all_coverages = self.get_final_coverages(pH_list, V_list)

        for pH in pH_list:
            if pH not in all_coverages:
                continue

            plt.figure(figsize=(10, 8))

            # Collect data for plotting
            species_data = {}
            for V in V_list:
                for species, coverage in all_coverages[pH].get(V, {}).items():
                    if species not in species_data:
                        species_data[species] = []
                    species_data[species].append(coverage)

            # Filter species with reasonable coverage values
            # Fixed HTML entities: &lt; -> <, &gt; -> >
            filtered_data = {}
            for species, coverages in species_data.items():
                if len(coverages) == len(V_list):  # Complete data
                    max_cov = max(coverages)
                    min_cov = min(coverages)
                    if max_cov <= 1 and min_cov >= 1e-20:  # Reasonable range
                        filtered_data[species] = coverages

            # Plot each species
            for species, coverages in filtered_data.items():
                label = self._format_species_name(species)
                plt.plot(V_list, coverages, label=label, linewidth=2, marker='o')

            # Formatting
            plt.xlabel('Potential (V)', fontsize=16, fontweight='bold')
            plt.ylabel('Coverage', fontsize=16, fontweight='bold')
            plt.title(f'Coverage vs Potential (pH = {pH})', fontsize=20, fontweight='bold')

            # Legend
            if filtered_data:
                legend_properties = {'weight': 'bold'}
                leg = plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                               prop=legend_properties, fontsize=12)
                leg.get_frame().set_edgecolor('black')
                leg.get_frame().set_linewidth(2.0)

            plt.xticks(fontweight='bold', fontsize=14)
            plt.yticks(fontweight='bold', fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            if save_plots:
                plt.savefig(plots_dir / f'coverage_pH_{pH}.png', dpi=300, bbox_inches='tight')
                logger.info(f"Saved plot: coverage_pH_{pH}.png")

            if show_plots:
                plt.show()
            else:
                plt.close()

    def _format_species_name(self, species: str) -> str:
        """Format species name for plotting (convert to subscripts)."""
        # Simple subscript conversion for common species
        normal = "0123456789"
        sub_s = "₀₁₂₃₄₅₆₇₈₉"
        trans_table = str.maketrans(normal, sub_s)

        formatted = species.translate(trans_table)

        # Move * to the beginning if present
        if '*' in formatted and not formatted.startswith('*'):
            formatted = formatted.replace('*', '')
            formatted = '*' + formatted

        return formatted

    def create_coverage_summary_table(self, pH_list: List[float], V_list: List[float], 
                                    save_csv: bool = True, output_path: str = "coverage_summary.csv") -> pd.DataFrame:
        """
        Create a summary table of final coverages.

        Args:
            pH_list: List of pH values
            V_list: List of potential values
            save_csv: Whether to save as CSV
            output_path: Path for CSV file

        Returns:
            DataFrame with coverage summary
        """
        all_coverages = self.get_final_coverages(pH_list, V_list)

        # Collect all unique species
        all_species = set()
        for pH_data in all_coverages.values():
            for V_data in pH_data.values():
                all_species.update(V_data.keys())

        # Create summary data
        summary_data = []
        for pH in pH_list:
            for V in V_list:
                row = {'pH': pH, 'V': V}
                for species in sorted(all_species):
                    coverage = all_coverages.get(pH, {}).get(V, {}).get(species, 0.0)
                    row[species] = coverage
                summary_data.append(row)

        df = pd.DataFrame(summary_data)

        if save_csv:
            df.to_csv(output_path, index=False)
            logger.info(f"Saved coverage summary: {output_path}")

        return df

def create_plots(pH_list: List[float], V_list: List[float], 
                base_directory: str = None, save_plots: bool = True) -> None:
    """
    Convenience function to create all plots.
    This replaces the original plot.py functionality with proper structure.

    Args:
        pH_list: List of pH values
        V_list: List of potential values  
        base_directory: Base directory containing results
        save_plots: Whether to save plots
    """
    plotter = CoveragePlotter(base_directory)

    try:
        # Create coverage vs potential plots
        plotter.plot_coverage_vs_potential(pH_list, V_list, save_plots=save_plots)

        # Create summary table
        plotter.create_coverage_summary_table(pH_list, V_list)

        logger.info("Plotting completed successfully")

    except Exception as e:
        logger.error(f"Error creating plots: {e}")
        raise
