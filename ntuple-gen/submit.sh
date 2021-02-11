#! /bin/bash
mkdir -p $1_results/log
mkdir -p $1_results/lhe
chmod +x submit.jdl
chmod +x wrapper.sh
condor_submit submit.jdl 
