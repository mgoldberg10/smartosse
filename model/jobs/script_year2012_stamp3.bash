#!/bin/bash -x
#SBATCH -J grace
#SBATCH -o grace.%j.out
#SBATCH -e grace.%j.err
#SBATCH -t 36:00:00
##SBATCH -t 2:00:00
##SBATCH -p skx-dev
#SBATCH -p skx
#SBATCH -N 13
#SBATCH -n 580 
##SBATCH -N 1
##SBATCH -n 28
#SBATCH -A OCE23001
#SBATCH --mail-user=matthew.goldberg10@utexas.edu
#SBATCH --mail-type=begin
#SBATCH --mail-type=end


#--- 0.load modules ------
echo $LD_LIBRARY_PATH
ulimit -s hard
ulimit -u hard
module purge; module load intel/24.0 impi/21.11 netcdf/4.9.2
source run_logic.sh

#---- 1.set variables ------
nprocs=580
snx=18
sny=18

#
pickupts0=0000000006
pickupts1=0000000007
extpickup=_it55warm
extsmooth=_9x1000mod
ext0=00
ext1=
ext4="_xx_clean"
ext5=
ext3=_v4r5obcspretanbl_GiV4r3_nlfs_adv30
use_optim=1
read_xx=1
#aster1_iter=62
forwadj="_ad_monbp_nofldcount_tamch_10x73x73"
#forwadj="_ad_daybp_nofldcount_tamch_10x73x73"
whichexp1=_adxOFF_20022023_capxxN50
#whichexp=_c68v
jobfile=script_grace.bash

mitgcm_version="c68v"
basedir=/work/08381/goldberg/ls6/MITgcm_${mitgcm_version}/mysetups/aste_270x450x180/osses
rtdir=/work/08381/goldberg/ls6/aste_270x450x180/run_template/
whichexp="_froman"
codedir=$basedir/code${whichexp}
builddir=$basedir/build${whichexp}
inputdir=$basedir/input_labsea_daily
#rundir=run${mitgcm_version}${whichexp}_natl_1month_alldailyxx_gracellc4320
rundir=run${mitgcm_version}${whichexp}_natl_1month_alldailyxx_gracellc4320_sc_may2026
#rundir=run${mitgcm_version}${whichexp}_natl_1month_alldailyxx_noapress
workdir_root_root=$SCRATCH/aste_270x450x180/osses/${rundir}

optimdir=${basedir}/OPTIM_grace
costfactors=(0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95 0.95)
#costfactors=(0.95)
itermax=$((${#costfactors[@]}-1))
coldstart="TRUE"

run_optim() {
    local iter=$1
    local iterprev=$2
    local costfactor=$3
    local optimext=$4
    local workdir=$5
    local dir_iter=$6
    local dir_iter_prev=$7
    local optimdir=$8
    local itermax=${9}
    local coldstart=${10}
    
    # 13. OPTIM
    cd ${optimdir}
    bash reset.bash
    
    cp ${dir_iter_prev}/m1qn3_output.txt ${optimdir}
    
    cp ${workdir}/ecco_cost_MIT_CE_000.opt${optimext} ${optimdir} 
    cp ${workdir}/ecco_ctrl_MIT_CE_000.opt${optimext} ${optimdir} 
    
    cp -f ${workdir}/costfunction${optimext} ${optimdir}
    cost=$(grep fc costfunction${optimext} | sed 's/D/E/g' | awk '{printf "%14.12e", $3}')
    costf=$(grep fc costfunction${optimext} | sed 's/D/E/g' | awk '{printf "%0.14f", $3}')
    echo "iter = $iter"
    echo "cost = $cost"
    
    costupdate=$(echo $costf*$costfactor | bc)
    costnew=$(echo $costupdate | awk '{printf "%14.12e\n", $costupdate}')
    echo "costnew = $costnew"
    
    # warm start after first optim iter
    #if [ ${iter} -gt 0 ]; then
    #  coldstart="FALSE"
    #fi
    
    mv data.optim data.optim_bk
    cat > data.optim <<EOF
          &OPTIM
          optimcycle=${iter},
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
  
    # \rm OP*
    ./optim.x > output_optim_it${optimext}.txt
  
    mkdir -p $dir_iter
    cp data.optim $dir_iter
    cp m1qn3_output.txt ${dir_iter}
    cp OPWARM.opt${optimext} ${dir_iter}
}

# Regions:

# Times:
# 2012: jan, apr, jul, oct
pickup_tss=(262944 269496 276048 282672)
mo_strs=(201201 201204 201207 201210)
ref_date="2011-12-31 23:40:00"
ndays=(31 30 31 31)
mo_strs=(2012)
ndays=(366)

for t in "${!pickup_tss[@]}"; do

    pickup_ts=${pickup_tss[t]}
    nday=${ndays[t]}
    mo_str=${mo_strs[t]}
    workdir_root=$workdir_root_root/${mo_str}

    case $mo_str in
        201204|201207|201210) continue ;;
    esac

    iter=0
    ext2=$(printf "%04d" $iter)
    iterstart=0
    
    while [ ! ${iter} -gt $itermax ]; do
        
        iterprev=$((iter-1))
        costfactor=${costfactors[${iter}]}
      
        optimext=$(printf "%04d" $iter)
        optimextprev=$(printf "%04d" $iterprev)
        
        workdir=$workdir_root/iter${optimext}
        dir_iter=${workdir}/run_optim/+it${optimext}
        dir_iter_prev=${workdir_root}/iter$optimextprev/run_optim/+it$optimextprev
    
#        if [ ${iter} -eq ${iterstart} ]; then
#            run_optim $iter $iterprev $costfactor $optimext $workdir $dir_iter $dir_iter_prev $optimdir $itermax $coldstart
#            let iter=iter+1
#          	continue
#        fi
    
        mkdir -p $workdir ;
        mkdir -p $workdir/tapes ;
        mkdir -p $workdir/profiles ;
        mkdir -p $workdir/diags
        
        cd $workdir;
        
        rm -f tapes/*
        rm -f profiles/*
        
        cp -rf ${codedir}/ .
        
        #--- 3. link forcing -------------
        ln -s /work/03901/atnguyen/jra55/ .
        
        \rm -f OB*
        ##iter0:
        ln -s ${rtdir}/input_obcs_r5i152/OB*x278_GiV4r3*_precipetan_bl*.bin .
        ln -s ${rtdir}/input_obcs_r3/OBEv_1260x50x290_allzeros.bin .
        ln -s ${rtdir}/input_obcs_r3/OBSu_1170x50x290_allzeros.bin .
        ln -s ${rtdir}/input_binaries/*.bin .
        ln -s ${rtdir}/input_weight/* .
        ln -s ${rtdir}/input_binaries/tile*.mitgrid .
        ln -s ${rtdir}/input_smooth/smooth2Dscales001${extsmooth} ./smooth2Dscales001
        ln -s ${rtdir}/input_smooth/smooth3DscalesH001${extsmooth} ./smooth3DscalesH001
        ln -s ${rtdir}/input_smooth/smooth3DscalesZ001 ./
        ln -s ${rtdir}/input_smooth/smooth2Dnorm001${extsmooth}.data ./smooth2Dnorm001.data
        ln -s ${rtdir}/input_smooth/smooth3Dnorm001${extsmooth}.data ./smooth3Dnorm001.data
        ln -s ${rtdir}/input_smooth/smooth2Dnorm001.meta ./
        ln -s ${rtdir}/input_smooth/smooth3Dnorm001.meta ./
        aste_bpweight_fname="bp_var_day_coarse4320_detide16constituent_std_cm"
	#aste_bp_fname="SMART_bp_2012_14x1350x270_gracemascon"
	aste_bp_fname="SMART_bp_2012_370x1350x270_daily"

        ln -s ${rtdir}/input_ecco/smart_phibot/grace_llc4320/$aste_bp_fname.bin ./$aste_bp_fname
        ln -s ${rtdir}/input_ecco/smart_phibot/$aste_bpweight_fname.bin $aste_bpweight_fname
        
        #=================================================================================
        #--- 6. NAMELISTS ---------
        cp -f ${inputdir}/* .
        
        # make diag directories
        grep -v '^#' data.diagnostics | grep -oP "filename\(\d+\) = '\K[^']+" | awk -F'/' '{print "diags/"$2}' | xargs -I{} mkdir -p {}
        
        cp -f ${basedir}/${jobfile} .
        
        cp -f data_profiles_${snx}x${sny}x${nprocs} data.profiles
        cp -f data_exch2_${snx}x${sny}x${nprocs} data.exch2
        
        # make modifications to data
    #    sed -i "s/^ select_rStar=2,/# select_rStar=2,/g" data
    #    sed -i "s/^ nonlinFreeSurf=4,/ nonlinFreeSurf=0,/g" data
    #    sed -i "s/^ useRealFreshWaterFlux=.*/ useRealFreshWaterFlux=.FALSE.,/g" data
        nt=$(echo $((nday*24*3600/1200)))
	nt=$(echo $((nt+1)))
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

	# smart cable osse:
        sed -i "/gencost_avgperiod(1)/s/month/day/" data.ecco
        sed -i "/gencost_barfile(1)/s/mon/day/" data.ecco
        
        #=================================================================================
        #--- 5. linking xx_ fields ------

        # sub in daily xx data.ctrl
        cp data.ctrl_dailyxx_multgen data.ctrl
#       cp data.ctrl_dailyxx_multgen_noapress data.ctrl
        cp data.exf_apressure data.exf
#       cp data.ctrl_dailyxx data.ctrl

    #    xxiter=000000${ext2}
        xxiter1=0062
        xxiter0=0000
        
        arr0=(kapredi kapgm salt theta logdiffkr apressure)
        dirXX0=${rtdir}/input_ADXX_iter${xxiter0}/
#        arr1=(atemp aqh precip lwdown swdown)
#        dirXX1=${rtdir}/input_ADXX_iter${xxiter1}_20022024_610/
#        arr2=(uwind vwind)
#        dirXX2=${rtdir}/input_ADXX_iter${xxiter1}_20122024_4888/
        arr1=(atemp aqh precip lwdown swdown uwind vwind)
        dirXX1=${rtdir}/input_ADXX_iter${xxiter1}_20122024_4888/
        
        if [ ${iter} -lt 1 ]; then
            for i in "${arr0[@]}"; do
              cp ${dirXX0}/xx_$i.000000${xxiter0}.data ./xx_$i.000000${ext2}.data
              echo $i
            done
            for i in "${arr1[@]}"; do
              cp ${dirXX1}/xx_$i.000000${xxiter1}.data ./xx_$i.000000${ext2}.data
              echo $i
            done
#            for i in "${arr2[@]}"; do
#              cp ${dirXX2}/xx_$i.000000${xxiter1}.data ./xx_$i.000000${ext2}.data
#              echo $i
#            done
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
        #start_date="${mo_str:0:4}-${mo_str:4:2}-01 00:00:00"
	mo_str=201201
        start_date="${mo_str:0:4}-${mo_str:4:2}-01 00:00:00"
        seconds_since_ref=$(( $(TZ=UTC date -d "$start_date" +%s) - $(TZ=UTC date -d "$ref_date" +%s) ))
        nIter0=$(awk "BEGIN {print int($seconds_since_ref / 1200 + 0.5)}")

        nIter0_1200=$pickup_ts
        sed -i "s/^ nIter0.*/ nIter0=${nIter0}.,/g" data
        pickupts0=$(printf "%010d" $nIter0_1200)
        pickupts1=$(printf "%010d" $nIter0)
        extpickup=""
        
        \rm -f pickup*
        pickupdir=${rtdir}/input_PICKUP/dt_1200/
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
            
        ##--- 11. run ----------------------------------
        date +%Y/%m/%d_%H:%M:%S.%3N > run.mitgcm.timing.txt
        #mpiexec -n ${nprocs} ${workdir}/mitgcmuv${forwadj}
        run_mitgcm_with_hang_check $nprocs $workdir $forwadj
        date +%Y/%m/%d_%H:%M:%S.%3N >> run.mitgcm.timing.txt
        
        rm w2*
        rm -r tapes
        
        #--- 13. OPTIM ---------------------------------
        run_optim $iter $iterprev $costfactor $optimext $workdir $dir_iter $dir_iter_prev $optimdir $itermax $coldstart
        
        let iter=iter+1
    done
done


