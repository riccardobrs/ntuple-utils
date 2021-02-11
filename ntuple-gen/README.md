Given a gridpack ZWm\_cHbox\_SM\_LI\_QU\_slc7\_amd64\_gcc700\_CMSSW\_10\_6\_0\_tarball.tar.xz lhe files have to be produced. Please copy the following scripts in the folder where gridpacks are stored in:

* wrapper.sh
* runcmsgrid.sh
* submit.jdl
* submit.sh

Check that the last line of submit.jdl is

    Queue 200 proc in (ZWm_cHbox_SM_LI_QU)

where 200 is the number of jobs (you can modify this number, if needed). The number of events per job is set in wrapper.sh. To complete the jobs submission on condor:

    ./submit.sh ZWm_cHbox_SM_LI_QU

Once the ZWm\_cHbox\_SM\_LI\_QU\_results production is completed, it can be postprocessed with

    python postProcess.py -b ZWm_cHbox_SM_LI_QU_results

Now you are ready to produce ntuples.