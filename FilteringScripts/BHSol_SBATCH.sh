#!/bin/bash
#SBATCH --job-name=PosyFilt
#SBATCH --output=./filt.out
#SBATCH --mem-per-cpu=10G
#SBATCH --time=0:10:00
#SBATCH --account=b1094
#SBATCH --partition=short
#SBATCH --mail-type=ALL
#SBATCH --mail-user=piersonlipschultz@gmail.com
export PATH_TO_POSYDON=/home/bku2126/b1095/bku2126/UCXBInvestigation/POSYDON
export PATH_TO_POSYDON_DATA=/projects/b1095/bku2126/POSYDON_tutorial/data
python BH-Sol_Filter.py /home/bku2126/b1095/bku2126/stellarBHs/grids/g4_.1_met/1e-02_Zsun_population.h5 -o /home/bku2126/b1095/bku2126/stellarBHs/Data/1e-02Zsun/ -overwrite False --maxPeriod 300