#!/usr/bin/env posydon_env_v2.2
import argparse
import sys
from pathlib import Path
import pandas as pd
from posydon.popsyn.synthetic_population import Population
from collections import Counter
from multiprocessing import Pool, cpu_count
import numpy as np
import time
from datetime import datetime


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
    """Worker receives a df chunk directly — no file I/O."""
    df_chunk, maxMass, maxPeriod = args

    BH_Sol_Mask = (
            (df_chunk['S1_state'] == 'BH') & (df_chunk['S2_state'] == 'H-rich_Core_H_burning')
            &  (df_chunk['state'] == 'detached')
            &  (df_chunk['S2_mass'] < float(maxMass)) & (df_chunk['orbital_period'] < float(maxPeriod))
            &  (df_chunk['S2_mass'] > .4)
            &  (df_chunk['time'] < 10e9)
        )

    PrevRowMask = BH_Sol_Mask.groupby(level=0).shift(-1, fill_value=False)
    AftRowMask  = BH_Sol_Mask.groupby(level=0).shift(1,  fill_value=False)

    return df_chunk[BH_Sol_Mask].copy(), df_chunk[PrevRowMask].copy(), df_chunk[AftRowMask].copy()


def process(pop, input_path, maxMass, maxPeriod, n_workers) -> tuple:
    """Filtering Logic. Returns full population file with calculated formation channels, as well as a .csv with the BH_sol rows"""

    bench = {}

    ### BH-MS_Detached filt
    BH_MS_FiltCond_Hist = "((S2_state == 'H-rich_Core_H_burning') & (S1_state == 'BH')) & (state == 'detached')"
    print('filtering pop for S1, S2, BH_MS')

    solBH_df_Hist = pd.DataFrame()
    t0 = time.perf_counter()
    try:
        solBH_df_Hist = pop.history.select(where=BH_MS_FiltCond_Hist)
    except Exception as e:
        print(f'WARNING!! found NO BH_MS-Detached systems: {e}')
    bench['select_s'] = time.perf_counter() - t0

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

    # load the full df once in the main process
    print(f'Loading {len(binary_indices)} candidate binaries...')
    t0 = time.perf_counter()
    df = pop.history[binary_indices]
    bench['hdf5_load_s'] = time.perf_counter() - t0

    # split the loaded DataFrame across workers — no file access in workers
    print(f'Filtering across {n_workers} workers...')
    chunks = np.array_split(df, n_workers)
    job_args = [(chunk, maxMass, maxPeriod) for chunk in chunks]

    t0 = time.perf_counter()
    with Pool(n_workers) as pool:
        results = pool.map(_filter_chunk, job_args)
    bench['parallel_filter_s'] = time.perf_counter() - t0

    filtPop_df = pd.concat([r[0] for r in results])
    PrevRow    = pd.concat([r[1] for r in results])
    AftRow     = pd.concat([r[2] for r in results])

    bench['n_candidates']  = len(binary_indices)
    bench['n_BH_Sol']      = len(filtPop_df)
    bench['n_workers']     = n_workers
    bench['total_s']       = bench['select_s'] + bench['hdf5_load_s'] + bench['parallel_filter_s']

    #### filt for failed systems
    ###fc = pop.formation_channels
    ##mask = fc['channel'] == 'ZAMS_oCE1_CC1_oRLO2_CC2_maxtime_END'
    ###:binary_indices_02Z = fc[mask].index.tolist()

   ###print(f'Found {len(filtPop_df)} BH-Sol Systems.')
    return filtPop_df, PrevRow, AftRow, bench


def write_benchmark(bench, run_dir: Path, input_path: Path, args):
    """Write benchmark summary to a .txt file in the run directory."""
    bench_path = run_dir / 'benchmark.txt'
    lines = [
        "=" * 50,
        "BH-Sol_Filter.py Benchmark Report",
        "=" * 50,
        f"Run timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Input file         : {input_path}",
        f"Output dir         : {run_dir}",
        f"maxMass            : {args.maxMass} Msun",
        f"maxPeriod          : {args.maxPeriod} days",
        f"n_workers          : {bench['n_workers']}",
        "-" * 50,
        f"HDF5 .select()     : {bench['select_s']:.2f}s",
        f"HDF5 index load    : {bench['hdf5_load_s']:.2f}s",
        f"Parallel filter    : {bench['parallel_filter_s']:.2f}s",
        f"Total              : {bench['total_s']:.2f}s",
        f"Wall time          : {bench['wall_time_s']:.2f}s",
        "-" * 50,
        f"Candidate binaries : {bench['n_candidates']:,}",
        f"BH-Sol systems     : {bench['n_BH_Sol']:,}",
        "=" * 50,
    ]
    bench_path.write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return bench_path


def write_outputs(pop, filtPop_df, PrevRow, AftRow, bench, base_output_dir: Path, outputName, overwriteBool, input_path, args):
    """Write both .csv and .h5, inside a dated run subfolder."""

    # create dated run folder: e.g. ./results/2026-05-28_LMXB_Filtered_1e+00_Zsun_population_filtRun/
    run_dir = base_output_dir / f"{datetime.now().strftime('%Y-%m-%d')}_{outputName}_filtRun"
    run_dir.mkdir(parents=True, exist_ok=True)

    pop_h5_OutputPath = (run_dir / outputName).with_suffix('.h5')
    df_csv_OutputPath = (run_dir / outputName)

    if pop_h5_OutputPath.exists() and not overwriteBool:
        raise FileExistsError(f'{pop_h5_OutputPath} already exists!! set overwrite to true or change FP.')
    if df_csv_OutputPath.exists() and not overwriteBool:
        raise FileExistsError(f'{pop_h5_OutputPath} already exists!! set overwrite to true or change FP.')

    pop.export_selection(filtPop_df.index.to_list(), (str(pop_h5_OutputPath)), append=False, overwrite=True)

    filtPop_df.to_csv(str(df_csv_OutputPath.with_suffix('.csv')))
    PrevRow.to_csv(str(((run_dir / (outputName + 'prevRow'))).with_suffix('.csv')))
    AftRow.to_csv(str(((run_dir / (outputName + 'AftRow'))).with_suffix('.csv')))

    bench_path = write_benchmark(bench, run_dir, input_path, args)

    return pop_h5_OutputPath, df_csv_OutputPath, bench_path


def main():
    t_total_start = time.perf_counter()

    args = parse_args()
    input_path = Path(args.input_file)

    try:
        validate_args(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    pop = read_input(input_path)
    filtPop_df, PrevRow, AftRow, bench = process(pop, input_path, args.maxMass, args.maxPeriod, args.n_workers)
    bench['wall_time_s'] = time.perf_counter() - t_total_start

    popPath, csvPath, benchPath = write_outputs(
        pop, filtPop_df, PrevRow, AftRow, bench,
        Path(args.output_dir), str(args.outputName),
        args.overwrite, input_path, args
    )

    print(f"Written: {popPath}")
    print(f"Written: {csvPath}")
    print(f"Written: {benchPath}")

if __name__ == "__main__":
    main()