#!/bin/bash
#SBATCH --job-name=1e_00_Zsun_Flt
#SBATCH --output=./filt.out
#SBATCH --mem-per-cpu=16G
#SBATCH --time=12:00:00
#SBATCH --account=b1094
#SBATCH --partition=ciera-std
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=piersonlipschultz@gmail.com
export PATH_TO_POSYDON=/home/bku2126/b1095/bku2126/UCXBInvestigation/POSYDON
export PATH_TO_POSYDON_DATA=/projects/b1095/bku2126/POSYDON_tutorial/data
python BH-Sol_Filter.py /home/bku2126/b1095/bku2126/stellarBHs/grids/g3/1e+00_Zsun_population.h5 -o /home/bku2126/b1095/bku2126/stellarBHs/Data/RandInitMassDistro/ -overwrite False --maxPeriod 300