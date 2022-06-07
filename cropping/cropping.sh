#!/bin/bash

#SBATCH -J crop
#SBATCH --output=slurm-%x.%j.out
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -t 20:00:00
#SBATCH --mem=2G

module load any/python/3.8.3-conda
conda activate mtproj

srcpath="/gpfs/space/projects/PerkinElmer/testis"
dstpath="/gpfs/space/projects/PerkinElmer/testis/crops_png"

python3 mtproject/cropping/crop_images.py --folders "$srcpath" --destination "$dstpath" --number 400000
