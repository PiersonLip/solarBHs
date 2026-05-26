#!/usr/bin/env posydon_env_v2.2
import argparse
import sys
from pathlib import Path
import pandas as pd
from posydon.popsyn.synthetic_population import Population
from collections import Counter
from multiprocessing import Pool, cpu_count
import numpy as np


### useage
# python BH-Sol_Filter.py /home/bku2126/b1095/bku2126/stellarBHs/Data/1e+00_Zsun_population.h5 -o ./testResults


# python BH-Sol_Filter.py /home/bku2126/b1095/bku2126/stellarBHs/grids/grid1/1e+00_Zsun_population.h5 -o ./3_24_26_Grid

def parse_args():
    parser = argparse.ArgumentParser(description="Filter pop .h5 file for low porb BH-Sol Binaries")
    parser.add_argument("input_file", help="Path to input file")
    parser.add_argument("-o", "--output-dir", default=".", help="Output directory (default: current dir)")
    parser.add_argument("-outputName", default=None, help="Filename for output files")
    parser.add_argument("-overwrite", default=False, help="Overwrite existing files with output.")
    parser.add_argument("--maxMass", default=3, help="(Solar) Upper mass limit for filtering")
    parser.add_argument("--maxPeriod", default=3.5, help="(Days) Upper period limit for filtering")
    parser.add_argument("--n_workers", default=cpu_count(), type=int, help="Number of parallel workers (default: all cores). Match to --cpus-per-task in SLURM.")

    return parser.parse_args()

def validate_args(args):
    input_path = Path(args.input_file)
    
    if input_path.suffix != ".h5":
        raise ValueError(f"Input file must be a .h5 population, got '{input_path.suffix}'")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if args.outputName == None:
        args.outputName = str('LMXB_Filtered_' + input_path.stem)


def read_input(input_path: Path):
    pop = Population(str(input_path))
    return pop


def _filter_chunk(args):
    """Worker function: each subprocess opens its own file handle and filters its chunk of binary indices."""
    input_path, index_chunk, maxMass, maxPeriod = args
    pop_chunk = Population(str(input_path))
    df = pop_chunk.history[index_chunk]

    BH_Sol_Mask = (
            (df['S1_state'] == 'BH') & (df['S2_state'] == 'H-rich_Core_H_burning')
            &  (df['state'] == 'detached')
            &  (df['S2_mass'] < float(maxMass)) & (df['orbital_period'] < float(maxPeriod))
            &  (df['S2_mass'] > .4)
            &  (df['time'] < 10e9)
        )

    PrevRowMask = BH_Sol_Mask.groupby(level=0).shift(-1, fill_value=False)
    AftRowMask  = BH_Sol_Mask.groupby(level=0).shift(1,  fill_value=False)

    return df[BH_Sol_Mask].copy(), df[PrevRowMask].copy(), df[AftRowMask].copy()


def process(pop, input_path, maxMass, maxPeriod, n_workers) -> tuple:
    """Filtering Logic. Returns full population file with calculated formation channels, as well as a .csv with the BH_sol rows"""

    ### BH-MS_Detached filt
    BH_MS_FiltCond_Hist = "((S2_state == 'H-rich_Core_H_burning') & (S1_state == 'BH')) & (state == 'detached')"
    print('filtering pop for S1, S2, BH_MS')

    solBH_df_Hist = pd.DataFrame()
    try:
        solBH_df_Hist = pop.history.select(where=BH_MS_FiltCond_Hist)
    except Exception as e:
        print(f'WARNING!! found NO BH_MS-Detached systems: {e}')

    print(f'found {len(solBH_df_Hist)} BH_MS-Detached systems')

    #### checking for S2 BHs and S1 MS 
    BH_MS_InverseFiltCond_Hist = "((S1_state == 'H-rich_Core_H_burning') & (S2_state == 'BH')) & (state == 'detached')"

    print('filtering pop for S2, S1, BH-Sol')
    try:
        solBH_Inverse_df_Hist = pop.history.select(where = BH_MS_InverseFiltCond_Hist)
        if len(solBH_Inverse_df_Hist) != 0: print (f'Warning!! Found {len(solBH_Inverse_df_Hist)} systems which S1:MS, S2:BH!! ')
    except:
        print('No S2, S1 BHs :)')

    ############################################
    ## actually filter for the BH_Sol systems ##
    ############################################

    binary_indices = solBH_df_Hist.index.unique().tolist()

    # split indices across workers and dispatch
    print(f'Filtering {len(binary_indices)} candidate binaries across {n_workers} workers...')
    chunks = np.array_split(binary_indices, n_workers)
    job_args = [(str(input_path), chunk.tolist(), maxMass, maxPeriod) for chunk in chunks]

    with Pool(n_workers) as pool:
        results = pool.map(_filter_chunk, job_args)

    filtPop_df = pd.concat([r[0] for r in results])
    PrevRow    = pd.concat([r[1] for r in results])
    AftRow     = pd.concat([r[2] for r in results])

    #### filt for failed systems
    ###fc = pop.formation_channels
    ##mask = fc['channel'] == 'ZAMS_oCE1_CC1_oRLO2_CC2_maxtime_END'
    ###:binary_indices_02Z = fc[mask].index.tolist()

   ###print(f'Found {len(filtPop_df)} BH-Sol Systems.')
    return filtPop_df, PrevRow, AftRow

def write_outputs(pop,filtPop_df, PrevRow, AftRow, output_dir: Path, outputName, overwriteBool):
    """Write both .csv and .h5."""

    output_dir.mkdir(parents=True, exist_ok=True)

    pop_h5_OutputPath = (output_dir / outputName).with_suffix('.h5')
    df_csv_OutputPath = (output_dir / outputName)
    
    if pop_h5_OutputPath.exists() and not overwriteBool:
        raise FileExistsError(f'{pop_h5_OutputPath} already exists!! set overwrite to true or change FP.')
    if df_csv_OutputPath.exists() and not overwriteBool:
        raise FileExistsError(f'{pop_h5_OutputPath} already exists!! set overwrite to true or change FP.')

    pop.export_selection(filtPop_df.index.to_list(), (str(pop_h5_OutputPath)), append=False, overwrite = True)
    
    filtPop_df.to_csv(str(df_csv_OutputPath.with_suffix('.csv')))
    PrevRow.to_csv(str(((output_dir / (outputName +'prevRow'))).with_suffix('.csv')))
    AftRow.to_csv(str(((output_dir / (outputName +'AftRow'))).with_suffix('.csv')))

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
    filtPop_df, PrevRow, AftRow = process(pop, input_path, args.maxMass, args.maxPeriod, args.n_workers)
    popPath, csvPath = write_outputs(pop, filtPop_df, PrevRow, AftRow, Path(args.output_dir), str(args.outputName), args.overwrite)

    print(f"Written: {popPath}")
    print(f"Written: {csvPath}")

if __name__ == "__main__":
    main()