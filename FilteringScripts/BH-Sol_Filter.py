#!/usr/bin/env posydon_env_v2.2
import argparse
import sys
from pathlib import Path
import pandas as pd
from posydon.popsyn.synthetic_population import Population
from collections import Counter


### useage
# python BH-Sol_Filter.py /home/bku2126/b1095/bku2126/stellarBHs/Data/1e+00_Zsun_population.h5 -o ./testResults

def parse_args():
    parser = argparse.ArgumentParser(description="Filter pop .h5 file for low porb BH-Sol Binaries")
    parser.add_argument("input_file", help="Path to input file")
    parser.add_argument("-o", "--output-dir", default=".", help="Output directory (default: current dir)")
    parser.add_argument("-outputName", default=None, help="Filename for output files")
    parser.add_argument("-overwrite", default=False, help="Overwrite existing files with output.")
    parser.add_argument("--maxMass", default=3, help="(Solar) Upper mass limit for filtering")
    parser.add_argument("--maxPeriod", default=3.5, help="(Days) Upper period limit for filtering")
    
    return parser.parse_args()

def validate_args(args):
    input_path = Path(args.input_file)
    
    if input_path.suffix != ".h5":
        raise ValueError(f"Input file must be a .h5 population, got '{input_path.suffix}'")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if args.outputName == None:
        args.outputName = str('BH_Sol_Filtered_' + input_path.stem)


def read_input(input_path: Path):
    pop = Population(str(input_path))
    return pop

def process(pop, maxMass, maxPeriod) -> tuple:
    """Filtering Logic — returns full population file with calculated formation channels, as well as a .csv with the BH_sol rows"""

    ### BH-MS_Detached filt
    BH_MS_FiltCond_Hist = "((S2_state == 'H-rich_Core_H_burning') & (S1_state == 'BH')) & (state == 'detached')"
    print('filtering pop for S1, S2, BH_MS')
    solBH_df_Hist = pop.history.select(where = BH_MS_FiltCond_Hist)
    print(f'found {len(solBH_df_Hist)} BH_MS-Detached systems')

    #### checking for S2 BHs and S1 MS 
    BH_MS_InverseFiltCond_Hist = "((S1_state == 'H-rich_Core_H_burning') & (S2_state == 'BH')) & (state == 'detached')"

    print('filtering pop for S2, S1, BH-Sol')
    solBH_Inverse_df_Hist = pop.history.select(where = BH_MS_InverseFiltCond_Hist)
    if len(solBH_Inverse_df_Hist) != 0: print (f'Warning!! Found {len(solBH_Inverse_df_Hist)} systems which S1:MS, S2:BH!! ')

    ############################################
    ## actually filter for the BH_Sol systems ##
    ############################################
    df = solBH_df_Hist

    filtPop_df = (
        df[
            (df['S1_state'] == 'BH') & (df['S2_state'] == 'H-rich_Core_H_burning')
            &  (df['state'] == 'detached')
            &  (df['S2_mass'] < maxMass) & (df['orbital_period'] < maxPeriod)
            &  (df['S2_mass'] > .1)
            &  (df['time'] < 10e9)
        ])
    
    df = None

    print(f'Found {len(filtPop_df)} BH-Sol Systems.')
    return filtPop_df

def write_outputs(pop,filtPop_df, output_dir: Path, outputName, overwrite):
    """Write both .csv and .h5."""

    output_dir.mkdir(parents=True, exist_ok=True)

    pop_h5_OutputPath = (output_dir / outputName).with_suffix('.h5')
    df_csv_OutputPath = (output_dir / outputName).with_suffix('.csv')
    
    if pop_h5_OutputPath.exists() and not overwrite:
        raise FileExistsError(f'{pop_h5_OutputPath} already exists!! set overwrite to true or change FP.')
    if df_csv_OutputPath.exists() and not overwrite:
        raise FileExistsError(f'{pop_h5_OutputPath} already exists!! set overwrite to true or change FP.')

    pop.export_selection(filtPop_df.index.to_list(), (str(pop_h5_OutputPath)), append=False, overwrite = True)
    
    filtPop_df.to_csv(str(df_csv_OutputPath))

    return pop_h5_OutputPath, df_csv_OutputPath

def main():
    args = parse_args()
    input_path = Path(args.input_file)
    
    try:
        validate_args(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    pop = read_input(input_path)
    filtPop_df = process(pop, args.maxMass, args.maxPeriod)
    popPath, csvPath = write_outputs(pop, filtPop_df, Path(args.output_dir), str(args.outputName), args.overwrite)

    print(f"Written: {popPath}")
    print(f"Written: {csvPath}")

if __name__ == "__main__":
    main()