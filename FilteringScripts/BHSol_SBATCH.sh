#!/bin/bash
#SBATCH --job-name=PosyFilt
#SBATCH --output=./filt.out
#SBATCH --mem-per-cpu=16G
#SBATCH --time=4:00:00
#SBATCH --account=b1095
#SBATCH --partition=grail-std
#SBATCH --mail-type=ALL
#SBATCH --mail-user=piersonlipschultz@gmail.com
#SBATCH --cpus-per-task=16
export PATH_TO_POSYDON=/home/bku2126/b1095/bku2126/UCXBInvestigation/POSYDON
export PATH_TO_POSYDON_DATA=/projects/b1095/bku2126/POSYDON_tutorial/data
python BH-Sol_Filter.py /home/bku2126/b1095/bku2126/1e+00_Zsun_population.h5 -o /home/bku2126/b1095/bku2126/stellarBHs/Data/10MillFilt -overwrite True --maxPeriod 300