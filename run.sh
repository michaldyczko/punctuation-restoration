#!/bin/bash -l
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4
#SBATCH -A g86-1042
#SBATCH --gres=gpu:1
#SBATCH --exclude=rysy-n7
#SBATCH --time=30:00:00
#SBATCH -o out.%j.out
#SBATCH -e err.%j.err

module use /home/marek357/calmsie/modules
module load python/python3.8/wav2docs
module av

if [ ! -e roberta_large_transformers ] ; then
    mkdir roberta_large_transformers &&  wget -q -O tmp.zip https://github.com/sdadas/polish-roberta/releases/download/models-transformers-v3.4.0/roberta_large_transformers.zip && unzip tmp.zip -d roberta_large_transformers && rm tmp.zip
else
    echo "----------- roberta_large_transformers FOUND -----------"
fi
echo "----------- TRAINING -----------"
python3 src/train.py --cuda=True --pretrained-model=roberta_large_transformers --freeze-bert=False --lstm-dim=-1 --language=poleval --seed=1 --lr=2e-5 --epoch=50 --use-crf=False --augment-type=all  --augment-rate=0.1 --alpha-sub=0.4 --alpha-del=0.4 --data-path=data --save-path=test_mgpu --batch-size=32 --sequence-length=256 --decay=0.01
