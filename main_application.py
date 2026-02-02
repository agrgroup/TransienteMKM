"""
Main application file for microkinetic modeling workflow.
Complete rewrite with proper structure and command-line interface.
"""

import argparse
import logging
from pathlib import Path
import sys

# Import our modules
from dependencies_fixed import *
from config import SolverSettings, load_config
from data_extraction import ExcelDataProcessor, data_extract
from simulation_runner import SimulationRunner, SimulationParameters
from plotting import CoveragePlotter, create_plots

logger = logging.getLogger(__name__)

class MicrokineticModeling:
    """Main application class for microkinetic modeling workflow."""

    def __init__(self, config_path: str = None):
        """
        Initialize application with configuration.

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = load_config(config_path)
        self.validate_setup()

    def validate_setup(self) -> None:
        """Validate configuration and setup."""
        errors = self.config.validate()
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise ValueError("Invalid configuration")

        logger.info("Configuration validated successfully")
        logger.info(f"pH range: {self.config.pH_list}")
        logger.info(f"V range: {self.config.V_list}")
        logger.info(f"Temperature: {self.config.temperature} K")

    def run_simulations(self) -> None:
        """Run all simulations for the parameter sweep."""
        logger.info("Starting simulation parameter sweep")

        # Initialize simulation runner
        runner = SimulationRunner(self.config)

        # Run parameter sweep using data extraction function
        runner.run_parameter_sweep(data_extract)

        logger.info("Simulation parameter sweep completed")

    def create_plots(self) -> None:
        """Create plots from simulation results."""
        if not self.config.create_plots:
            logger.info("Plotting disabled in configuration")
            return

        logger.info("Creating plots from simulation results")

        create_plots(
            pH_list=self.config.pH_list,
            V_list=self.config.V_list,
            base_directory=self.config.output_base_dir,
            save_plots=True
        )

        logger.info("Plotting completed")

    def run_full_workflow(self) -> None:
        """Run the complete workflow: simulations + plotting."""
        try:
            self.run_simulations()
            self.create_plots()
            logger.info("Full workflow completed successfully")

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise

    def export_config(self, output_path: str) -> None:
        """Export current configuration to file."""
        if output_path.endswith('.yaml') or output_path.endswith('.yml'):
            self.config.to_yaml(output_path)
        elif output_path.endswith('.json'):
            self.config.to_json(output_path)
        else:
            raise ValueError("Config file must be .yaml, .yml, or .json")

        logger.info(f"Configuration exported to: {output_path}")

def create_example_config() -> None:
    """Create an example configuration file."""
    config = SolverSettings()
    config.pH_list = [7, 10, 13]
    config.V_list = [0, -0.2, -0.4, -0.6, -0.8, -1.0]
    config.executable_path = "/path/to/your/mkmcxx.exe"
    config.input_excel_path = "input.xlsx"

    config.to_yaml("example_config.yaml")
    config.to_json("example_config.json")

    print("Created example configuration files:")
    print("  - example_config.yaml")  
    print("  - example_config.json")

def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(description='Microkinetic Modeling Workflow')

    parser.add_argument('--config', '-c', type=str, 
                       help='Path to configuration file')
    parser.add_argument('--simulations-only', action='store_true',
                       help='Run only simulations (no plotting)')
    parser.add_argument('--plots-only', action='store_true', 
                       help='Create only plots (no simulations)')
    parser.add_argument('--create-example-config', action='store_true',
                       help='Create example configuration files')
    parser.add_argument('--export-config', type=str,
                       help='Export current config to specified file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    parser.add_argument('--sweep-mode', action='store_true', help='Enable sweep mode with coverage propagation')
    parser.add_argument('--sweep-rate', type=float, default=0.1, help='Sweep rate in V/s (default: 0.1)')
    parser.add_argument('--no-coverage-propagation', action='store_true', help='Disable coverage propagation in sweep mode')

    args = parser.parse_args()

    # Set up logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handle special commands
    if args.create_example_config:
        create_example_config()
        return

    try:
        # Initialize application
        app = MicrokineticModeling(args.config)

        if any(isinstance(v, list) for v in app.config.V_list):
            # flatten one level
            app.config.V_list = [float(x) for sub in app.config.V_list for x in sub]
            logger.warning(f"Flattened nested V_list → {app.config.V_list}")

        # Override sweep mode settings from command line
        if args.sweep_mode:
            app.config.enable_sweep_mode = True
            app.config.sweep_rate = args.sweep_rate
            app.config.use_coverage_propagation = not args.no_coverage_propagation
            logger.info(f"Sweep mode enabled: {args.sweep_rate} V/s, coverage propagation: {not args.no_coverage_propagation}")

        # Handle config export
        if args.export_config:
            app.export_config(args.export_config)
            return

        # Run workflow based on arguments
        if args.simulations_only:
            app.run_simulations()
        elif args.plots_only:
            app.create_plots()
        else:
            app.run_full_workflow()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
