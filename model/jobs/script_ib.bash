#!/bin/bash -x
#PBS -N mitgcm
#PBS -l select=15:ncpus=40:model=sky_ele
#PBS -l walltime=02:00:00
##PBS -l walltime=00:05:00
##PBS -q devel
#PBS -q normal
#PBS -o ib.out
#PBS -e ib.err

#==================================================
# 0. MODULES
#==================================================
echo $LD_LIBRARY_PATH
ulimit -s hard
ulimit -u hard
source run_logic.sh

#==================================================
# 1. SETTINGS
#==================================================

nprocs=580
snx=18
sny=18

costfactor=0.95
itermax=0
coldstart="TRUE"

forwadj="_ad_daybp_nofldcount_tamch_10x73x73"
mitgcm_version="c68v"
extsmooth=_9x1000mod
whichexp="_froman"
basedir=$NOBACKUP/MITgcm_${mitgcm_version}/mysetups/aste_270x450x180/osses
anscratchdir=/nobackupp17/atnguye4/llc270/aste_270x450x180/
rtdir=$anscratchdir/run_template/
scratchdir=$NOBACKUP/aste_270x450x180
codedir=$basedir/code${whichexp}
builddir=$basedir/build${whichexp}
inputdir=$basedir/input_labsea_daily
rundir=run${mitgcm_version}${whichexp}_ib_freq2
workdir_root_root_root=$scratchdir/osses/${rundir}
optimdir=${basedir}/OPTIM_subgyre

#==================================================
# IB EXPERIMENT SETTINGS
#==================================================

ctrl_freqs=(24 36 48 60 72 84 96)
ctrl_freqs=(240 120)

pickup_ts=262944
mo_str=201201
nday=7
ref_date="2011-12-31 23:40:00"

#==================================================
# FUNCTIONS
#==================================================

iter_complete () {
    local wdir=$1
    local cost_file ctrl_file
    cost_file=$(compgen -G "${wdir}/ecco*cost*")
    ctrl_file=$(compgen -G "${wdir}/ecco*ctrl*")
    [[ -n "$cost_file" && -n "$ctrl_file" ]]
}

find_next_iter () {
    local root=$1
    for (( i=0; i<=itermax; i++ )); do
        iterdir=$(printf "%s/iter%04d" "$root" "$i")
        if ! iter_complete "$iterdir"; then
            echo $i
            return
        fi
    done
    echo -1
}

run_optim() {

    local iter=$1
    local iterprev=$((iter-1))
    local optimext=$(printf "%04d" $iter)
    local optimextprev=$(printf "%04d" $iterprev)

    local workdir=$2
    local workdir_prev=$3

    local dir_iter=${workdir}/run_optim/+it${optimext}
    local dir_iter_prev=${workdir_prev}/run_optim/+it${optimextprev}

    cd ${optimdir}
    bash reset.bash

    cp ${dir_iter_prev}/m1qn3_output.txt .
    cp ${workdir_prev}/ecco_cost_MIT_CE_000.opt${optimextprev} .
    cp ${workdir_prev}/ecco_ctrl_MIT_CE_000.opt${optimextprev} .
    cf=${workdir_prev}/costfunction${optimextprev}
    cp $cf .

    cost=$(grep fc ${cf} | sed 's/D/E/g' | awk '{printf "%14.12e", $3}')
    costf=$(grep fc ${cf} | sed 's/D/E/g' | awk '{printf "%0.14f", $3}')
    costupdate=$(echo $costf*$costfactor | bc)
    costnew=$(printf "%14.12e\n" $costupdate)

    mv data.optim data.optim_bk

cat > data.optim <<EOF
 &OPTIM
 optimcycle=${iterprev},
 numiter=10,
 nfunc=9,
 fmin=${costnew},
 iprint=10,
 nupdate=4,
 /
 &M1QN3
 coldstart = .${coldstart}.,
 /
EOF

    ./optim.x > output_optim_it${optimext}.txt

    mkdir -p $dir_iter
    cp data.optim $dir_iter
    cp m1qn3_output.txt $dir_iter
    cp OPWARM.opt${optimext} $dir_iter
}

#==================================================
# MAIN LOOP OVER CONTROL FREQUENCIES
#==================================================

for ctrl_freq in "${ctrl_freqs[@]}"; do

    echo "======================================="
    echo "CTRL FREQ = ${ctrl_freq} hr"
    echo "======================================="

    ctrl_freq_seconds=$((ctrl_freq * 3600))
    ctrl_freq_dir=${scratchdir}/run_template/input_ADXX_iter0062_20122024_4888/ib_freqs/${ctrl_freq}hr

    workdir_root=${workdir_root_root_root}/${mo_str}/${ctrl_freq}hr

    while true; do

        iter=$(find_next_iter "$workdir_root")

        if [[ $iter -lt 0 ]]; then
            echo "DONE freq ${ctrl_freq}"
            break
        fi

        optimext=$(printf "%04d" $iter)
        workdir=${workdir_root}/iter${optimext}
        workdir_prev=$(printf "%s/iter%04d" "$workdir_root" "$((iter-1))")

        echo "Running iter ${optimext} @ ${ctrl_freq}hr"

        mkdir -p $workdir/{tapes,profiles,diags}
        cd $workdir || exit 1

        rm -f tapes/* profiles/*
        cp -rf ${codedir}/ .

        #--------------------------------------
        # FORCING + LINKS (UNCHANGED)
        #--------------------------------------

        ln -s /nobackupp17/atnguye4/jra55/ .
        
        \rm -f OB*
        ##iter0:
        ln -s ${scratchdir}/run_template/input_obcs_r5i152/OB*x278_GiV4r3*_precipetan_bl*.bin .
        ln -s ${scratchdir}/run_template/input_obcs_r3/OBEv_1260x50x290_allzeros.bin .
        ln -s ${scratchdir}/run_template/input_obcs_r3/OBSu_1170x50x290_allzeros.bin .
        ln -s ${rtdir}/input_binaries/*.bin .
        ln -s ${scratchdir}/run_template/input_weight/* .
        ln -s ${rtdir}/input_binaries/tile*.mitgrid .
        ln -s ${rtdir}/input_smooth/smooth2Dscales001${extsmooth} ./smooth2Dscales001
        ln -s ${rtdir}/input_smooth/smooth3DscalesH001${extsmooth} ./smooth3DscalesH001
        ln -s ${rtdir}/input_smooth/smooth3DscalesZ001 ./
        ln -s ${rtdir}/input_smooth/smooth2Dnorm001${extsmooth}.data ./smooth2Dnorm001.data
        ln -s ${rtdir}/input_smooth/smooth3Dnorm001${extsmooth}.data ./smooth3Dnorm001.data
        ln -s ${rtdir}/input_smooth/smooth2Dnorm001.meta ./
        ln -s ${rtdir}/input_smooth/smooth3Dnorm001.meta ./
        aste_bpweight_fname="bp_var_day_coarse4320_detide16constituent_std_cm"
        region_str=$(echo $region | cut -d '_' -f1)
        aste_bp_fname="SMART_bp_detide16constituents_detrend_201201_31x1350x270_142sensors_fullnatl_last2of7days"
        ln -s ${scratchdir}/run_template//input_ecco/smart_phibot/one_month_daily_bp_experiments/last2of7days/$aste_bp_fname.bin ./$aste_bp_fname
        ln -s ${scratchdir}/run_template//input_ecco/smart_phibot/$aste_bpweight_fname.bin $aste_bpweight_fname
        
        #=================================================================================
        #--- 6. NAMELISTS ---------
        cp -f ${inputdir}/* .
        
        # make diag directories
        grep -v '^#' data.diagnostics | grep -oP "filename\(\d+\) = '\K[^']+" | awk -F'/' '{print "diags/"$2}' | xargs -I{} mkdir -p {}
        
        cp -f ${basedir}/${jobfile} .
        
        cp -f data_profiles_${snx}x${sny}x${nprocs} data.profiles
        cp -f data_exch2_${snx}x${sny}x${nprocs} data.exch2
        cp data.exf_apressure data.exf
        
        # make modifications to data
        sed -i "s/^ select_rStar=2,/# select_rStar=2,/g" data
        sed -i "s/^ nonlinFreeSurf=4,/ nonlinFreeSurf=0,/g" data
        sed -i "s/^ useRealFreshWaterFlux=.*/ useRealFreshWaterFlux=.FALSE.,/g" data
        nt=$(echo $((nday*24*3600/1200)))
        monitorFreq=86400
        deltaT=1200
        deltaTtracer=1200
        deltaTmom=1200
        sed -i "s/^ nTimeSteps.*/ nTimeSteps=${nt},/g" data
        sed -i "s/^ monitorFreq.*/ monitorFreq=${monitorFreq}.0,/g" data
        sed -i "s/^ deltaT.*/ deltaT=${deltaT}.,/g" data
        sed -i "s/^ deltaTmom.*/ deltaTmom=${deltaTmom}.,/g" data
        sed -i "s/^ deltaTtracer.*/ deltaTtracer=${deltaTtracer},/g" data
        
        # data.ecco
        sed -i "s/gencost_datafile(1).*/gencost_datafile(1) = \'${aste_bp_fname}\',/" data.ecco
        sed -i "s/gencost_errfile(1).*/gencost_errfile(1) = \'${aste_bpweight_fname}\',/" data.ecco
        sed -i "/gencost_avgperiod(1)/s/month/day/" data.ecco
        sed -i "/gencost_barfile(1)/s/mon/day/" data.ecco
    
        cp data.ctrl_dailyxx_multgen data.ctrl
        sed -i "s/xx_gentim2d_period(\([0-9]\+\))=[0-9.]\+,/xx_gentim2d_period(\1)=${ctrl_freq_seconds}.0,/" data.ctrl

        #--------------------------------------
        # XX FIELDS (FREQ-DEPENDENT)
        #--------------------------------------

        ext2=$(printf "%04d" $iter)
        xxiter=000000${ext2}
        xxiter1=0062
        xxiter0=0000
        
        arr0=(kapredi kapgm salt theta logdiffkr apressure)
        dirXX0=${scratchdir}/run_template/input_ADXX_iter${xxiter0}/
        arr1=(atemp aqh precip lwdown swdown uwind vwind)
        
        if [ ${iter} -lt 1 ]; then
            for i in "${arr0[@]}"; do
              cp ${dirXX0}/xx_$i.000000${xxiter0}.data ./xx_$i.000000${ext2}.data
              echo $i
            done
            for i in "${arr1[@]}"; do
              cp ${ctrl_freq_dir}/xx_$i.0000000062.data ./xx_$i.000000${ext2}.data
              echo $i
            done
            sed -i -e 's/'"doinitxx = .*"'/'"doinitxx = .FALSE."'/g' data.ctrl
            sed -i -e 's/'"doMainUnpack = .*"'/'"doMainUnpack = .FALSE."'/g' data.ctrl
            sed -i -e 's/'"doMainPack = .*"'/'"doMainPack = .TRUE."'/g' data.ctrl
        else
          cp -f ${optimdir}/ecco_ctrl_MIT_CE_000.opt${optimext} ./
          sed -i -e 's/'"doinitxx = .*"'/'"doinitxx = .FALSE."'/g' data.ctrl
          sed -i -e 's/'"doMainUnpack = .*"'/'"doMainUnpack = .TRUE."'/g' data.ctrl
          sed -i -e 's/'"doMainPack = .*"'/'"doMainPack = .TRUE."'/g' data.ctrl
        fi


        # shift calendar to day before $mo_str-01
        cp data.cal_20120101 data.cal
        #prev_day=$(date -d "${mo_str}01 -1 day" +"%Y%m%d")
        #sed -i "s/^ startDate_1=.*/ startDate_1=${prev_day},/" data.cal
        
        #=================================================================================
        
        #--- 7. executable --------
        \rm -f mitgcmuv*
        cp -f ${builddir}/mitgcmuv${forwadj}_${snx}x${sny}x${nprocs} ./mitgcmuv${forwadj}
        cp -f ${builddir}/tamc.h ./
        cp -f ${builddir}/Makefile ./
        
        #--- 8. pickups -----------
        #NOTE: for pickup: copy instead of link to prevent accidental over-write
        #nIter0=473328 # jan 01 2011
        #nIter0=510048
    
        
        # compute nIter0 relative to ref_date
        start_date="${mo_str:0:4}-${mo_str:4:2}-01 00:00:00"
        seconds_since_ref=$(( $(TZ=UTC date -d "$start_date" +%s) - $(TZ=UTC date -d "$ref_date" +%s) ))
        nIter0=$(awk "BEGIN {print int($seconds_since_ref / 1200 + 0.5)}")
    
        nIter0_1200=$pickup_ts
        sed -i "s/^ nIter0.*/ nIter0=${nIter0}.,/g" data
        pickupts0=$(printf "%010d" $nIter0_1200)
        pickupts1=$(printf "%010d" $nIter0)
        extpickup=""
        
        \rm -f pickup*
        pickupdir=${scratchdir}/run_template/input_PICKUP/dt_1200/
        cp -f ${pickupdir}/pickup${extpickup}.${pickupts0}.data ./pickup.${pickupts1}.data
        cp -f ${pickupdir}/pickup${extpickup}.${pickupts0}.meta ./pickup.${pickupts1}.meta
        cp -f ${pickupdir}/pickup_seaice${extpickup}.${pickupts0}.data ./pickup_seaice.${pickupts1}.data
        cp -f ${pickupdir}/pickup_seaice${extpickup}.${pickupts0}.meta ./pickup_seaice.${pickupts1}.meta
        
        #--- 9. make a list of all linked files ------
        
        \rm -f command_ln_input
        ls -l input*/* > command_ln_input
        \rm -f command_ln_binary
        ls -l *.nc > command_ln_binary
        ls -l *.bin >> command_ln_binary
        ls -l tile* >> command_ln_binary
        ls -l smooth* >> command_ln_binary
        ls -l xx* >> command_ln_binary
        
        #--- 10. (re)set optimcycle --------------------
        
        \rm data.optim
        cat > data.optim <<EOF
             &OPTIM
             optimcycle=${iter},
             /
EOF
                
        date +%Y/%m/%d_%H:%M:%S.%3N > run.mitgcm.timing.txt
    #    run_mitgcm_with_hang_check $nprocs $workdir $forwadj
        mpiexec -n ${nprocs} ./mitgcmuv${forwadj}
        date +%Y/%m/%d_%H:%M:%S.%3N >> run.mitgcm.timing.txt
    
        rm -f w2*
        rm -rf tapes
        find . -type f \( -name 'STDOUT*' ! -name 'STDOUT.0000' -o -name 'STDERR*' ! -name 'STDERR.0000' \) -delete
    
    done
done
