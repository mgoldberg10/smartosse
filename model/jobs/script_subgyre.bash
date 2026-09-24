#!/bin/bash
#PBS -N mitgcm
#PBS -l select=29:ncpus=20:model=ivy
#PBS -l walltime=38:00:00
#PBS -q long
#PBS -o aste_sg_phibot.out
#PBS -e aste_sg_phibot.err


#--- 0.load modules ------
#ulimit -s unlimited
module purge
module load comp-intel/2018.3.222
module load szip/2.1.1
module load mpi-hpe/mpt
module load hdf4/4.2.12
module load hdf5/1.8.18_mpt
module load netcdf/4.4.1.1_mpt

echo $LD_LIBRARY_PATH
ulimit -s hard
ulimit -u hard

#---- 1.set variables ------
nprocs=580
snx=18
sny=18
#nprocs=242
#snx=30
#sny=30
pickupts0="0000000006"
# 2002-01-01
pickupts1="0000000007"
# 2011-01-01
pickupts1="0000508320"
extpickup=""
extsmooth="_9x1000mod"
ext4=
ext3="_v4r5obcspretanbl_GiV4r3_nlfs_adv30"
iter=0
forwadj="_ad_tamch_10x73x73"

whichexp="_phibot"
jobfile=script_subgyre.bash

ext2=$(printf "%04d" $iter)

#--- 2.set dir ------------
mitgcm_version="c68v"
basedir=$NOBACKUP/MITgcm_${mitgcm_version}/mysetups/aste_270x450x180/osses
anscratchdir=/nobackupp17/atnguye4/llc270/aste_270x450x180/
scratchdir=$NOBACKUP/aste_270x450x180
codedir=$basedir/code${whichexp}
builddir=$basedir/build${whichexp}
inputdir=$basedir/input${whichexp}
rundir=run${mitgcm_version}${whichexp}_fullNR_subgyre_coldstart_${ext3}_${nprocs}_it${ext2}_pk${pickupts1}
workdir_root=$scratchdir/osses/${rundir}

optimdir=${basedir}/OPTIM_subgyre
costfactors=(0.95 0.95 0.98 0.98 0.98 0.98 0.98 0.98 0.98 0.98 0.98 0.98)
#costfactors=(0.95 0.95)
iter=0
iterstart=0
itermax=$((${#costfactors[@]}-1))
#itermax=0
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

while [ ! ${iter} -gt $itermax ]; do
#    if [ ${iter} -lt ${iterstart} ]; then
#        let iter=iter+1
#        continue
#    fi

    iterprev=$((iter-1))
    costfactor=${costfactors[${iter}]}
  
    optimext=$(printf "%04d" $iter)
    optimextprev=$(printf "%04d" $iterprev)
    
    workdir=$workdir_root/iter${optimext}
    dir_iter=${workdir}/run_optim/+it${optimext}
    dir_iter_prev=${workdir_root}/iter$optimextprev/run_optim/+it$optimextprev

    if [ ${iter} -eq ${iterstart} ]; then
        run_optim $iter $iterprev $costfactor $optimext $workdir $dir_iter $dir_iter_prev $optimdir $itermax $coldstart
        let iter=iter+1
        continue
    fi

    mkdir -p $workdir;
    mkdir -p $workdir/tapes;
    mkdir -p $workdir/profiles;
    mkdir -p $workdir/diags;

    cd $workdir;
    rm -f tapes/*
    rm -f profiles/*
    
    cp -rf ${codedir}/ .
    
    #--- 3. link forcing -------------
    ln -s $NOBACKUP/jra55 .
    
    #--- 4. linking binary ---------
    ln -s ${anscratchdir}/run_template/input_binaries/*.bin .
    ln -s ${anscratchdir}/run_template/input_bathymetry/*.bin .
    ln -s ${anscratchdir}/run_template/input* .
    ln -s ${anscratchdir}/run_template/input_weight/* .
    ln -s ${anscratchdir}/run_template/input_binaries/tile*.mitgrid .
    ln -s ${scratchdir}/run_template/input_obcs/input_obcs_r5i152/OB*_GiV4r3*_precipetan_bl*.bin .
    ln -s ${scratchdir}/run_template/input_obcs/input_obcs_r3/OBEv_1260x50x290_allzeros.bin .
    ln -s ${scratchdir}/run_template/input_obcs/input_obcs_r3/OBSu_1170x50x290_allzeros.bin .
    ###
    ln -s ${anscratchdir}/run_template/input_smooth/smooth2Dscales001${extsmooth} ./smooth2Dscales001
    ln -s ${anscratchdir}/run_template/input_smooth/smooth3DscalesH001${extsmooth} ./smooth3DscalesH001
    ln -s ${anscratchdir}/run_template/input_smooth/smooth3DscalesZ001 ./
    ln -s ${anscratchdir}/run_template/input_smooth/smooth2Dnorm001${extsmooth}.data ./smooth2Dnorm001.data
    ln -s ${anscratchdir}/run_template/input_smooth/smooth3Dnorm001${extsmooth}.data ./smooth3Dnorm001.data
    ln -s ${anscratchdir}/run_template/input_smooth/smooth2Dnorm001.meta ./
    ln -s ${anscratchdir}/run_template/input_smooth/smooth3Dnorm001.meta ./
    ln -s ${scratchdir}/run_template/input_ecco/aste_ones.bin ./aste_ones
    ln -s ${scratchdir}/run_template/input_ecco/aste_ones.bin ./aste_ones.data
    ln -s ${scratchdir}/run_template/input_clim/* ./

    aste_bpweight_fname="aste_coarse4320_bp_weight_detrend_equivheight"
    aste_bp_fname="SMART_bp_detide_detrend_mo_20x1350x270_25_subgyre"
    ln -s ${scratchdir}/run_template/input_ecco/smart_phibot/$aste_bp_fname.bin ./$aste_bp_fname
    ln -s ${scratchdir}/run_template/input_ecco/smart_phibot/$aste_bpweight_fname.bin $aste_bpweight_fname
    
    #=================================================================================

    #--- 5. NAMELISTS ---------
    cp -f ${basedir}/${jobfile} .
    cp -f ${inputdir}/* .

    ##--- 6. linking xx_ fields ------
    xxiter=000000${ext2}
    xxiter1=0062
    xxiter0=0000
    
    ###iter0:
    ##set arr0=(kapredi kapgm salt theta logdiffkr aqh atemp uwind vwind precip)
    ##set arr1=(lwdown swdown)
    ###iter62:
    ##3D fields have already been mapped into pickups and input files
    ## so we're reading in a set of zeros:
    declare -a arr0=("kapredi" "kapgm" "salt" "theta" "logdiffkr")
    dirXX0=${anscratchdir}/run_template/input_ADXX_iter${xxiter0}/
    ##2D time-varying fields were not mapped into jra55 because it cannot
    ##be done accurately in the Arctic.  As a result, need iter62 xx files:
    declare -a arr1=("atemp" "aqh" "uwind" "vwind" "precip" "lwdown" "swdown" "tauu" "tauv")
    #dirXX1=${anscratchdir}/run_template/input_ADXX_iter${xxiter1}_20022022_558/
    dirXX1=${scratchdir}/run_template/input_ADXX_iter${xxiter1}_20022024_610
    
    ##  #if [ ${iter} -lt 13 ]; then
    for i in "${arr1[@]}"; do
      echo $i
      fname=xx_$i.000000${xxiter1}.data
      if [ ! -e ${workdir}/${fname} ]; then
        cp ${dirXX1}/${fname} $workdir/xx_$i.${xxiter}.data
      #cp ${dirXX1}/xx_${arr1[$i]}.000000${xxiter1}.meta    ./xx_${arr1[$i]}.${xxiter}.meta
      fi
    done
    #
    for i in "${arr0[@]}"; do
      echo $i
      fname=xx_$i.000000${xxiter0}.data
      if [ ! -e ${workdir}/${fname} ]; then
        cp ${dirXX0}/${fname} $workdir/xx_$i.${xxiter}.data
        #cp ${dirXX0}/xx_${arr0[$i]}.000000${xxiter0}.meta ./xx_${arr0[$i]}.${xxiter}.meta
      fi
    done
      
#    if [ ${iter} -eq 0 ]; then
#      ## set ctrl period, link dummy files
#      gentim2d_files=$(grep "^ xx_gentim2d_file" data.ctrl | cut -d "'" -f2)
#      iter_ext=$(printf "%010d" $iter)
#      for gentim2d_file in $gentim2d_files;do
#        fname=$gentim2d_file.$iter_ext
#        rm ${workdir_root}/$fname.data
#        ln -s ${scratchdir}/run_template/input_xx/zeros_270x1350x506.bin ${workdir_root}/$fname.data
#      done
#
#      # link from workdir_root to this iter directory
#      for f in `ls $workdir_root/xx*`; do
#        filename=$(basename $f)
#        rm $workdir/$filename
#        ln -s $f $workdir
#      done
#    fi

    #=================================================================================

    
    #ctrl_weights=$(grep "^ xx_gentim2d_weight" input_obssens/data.ctrl | cut -d "'" -f2)
    #for ctrl_weight in $ctrl_weights; do
    #  ln -s ${scratchdir}/run_template/input_weights/$ctrl_weight .
    #done
    
    # non/linear free surface
    sed -i "s/^ select_rStar=2,/# select_rStar=2,/g" data
    sed -i "s/^ nonlinFreeSurf=4,/ nonlinFreeSurf=0,/g" data
    sed -i "s/^ useRealFreshWaterFlux=.*/ useRealFreshWaterFlux=.FALSE.,/g" data

    ### delta=1200
    # 430 days year: 30959
    # three months: 6552
    nt=35136
#    nt=10
    monitorFreq=2635200
#    monitorFreq=86400
    #monitorFreq=86400
    #adjMonitorFreq=600
    deltaT=1200
    deltaTtracer=1200
    deltaTmom=1200
    sed -i "s/^ nTimeSteps.*/ nTimeSteps=${nt},/g" data
    sed -i "s/^ monitorFreq.*/ monitorFreq=${monitorFreq}.0,/g" data
    sed -i "s/^ deltaT.*/ deltaT=${deltaT}.,/g" data
    sed -i "s/^ deltaTmom.*/ deltaTmom=${deltaTmom}.,/g" data
    sed -i "s/^ deltaTtracer.*/ deltaTtracer=${deltaTtracer},/g" data

    # pickupts1="0000508320"
#    nIter0=254160
    nIter0=255024 # sept 13 2011
    sed -i "s/^ nIter0.*/ nIter0=${nIter0}.,/g" data
    pickupts1200=$(printf "%010d" $nIter0)

    # daily diags
    sed -i -E 's/(frequency\([0-9]+\) = )[0-9.]+/\12635200.0/' data.diagnostics
    grep -v '^#' data.diagnostics | grep -oP "filename\(\d+\) = '\K[^']+" | awk -F'/' '{print "diags/"$2}' | xargs -I{} mkdir -p {}

    # data.ecco
    sed -i "s/gencost_datafile(1).*/gencost_datafile(1) = \'${aste_bp_fname}\',/" data.ecco
    sed -i "s/gencost_errfile(1).*/gencost_errfile(1) = \'${aste_bpweight_fname}\',/" data.ecco

    cp -f data_exch2_${snx}x${sny}x${nprocs} data.exch2
    
    #-- swap out data.ctrl
    # begin from An's optimized aste controls, then for future iters use updated controls
    if [ ${iter} -lt 1 ]; then
      sed -i -e 's/'"doinitxx = .*"'/'"doinitxx = .FALSE."'/g' data.ctrl
      sed -i -e 's/'"doMainUnpack = .*"'/'"doMainUnpack = .FALSE."'/g' data.ctrl
      sed -i -e 's/'"doMainPack = .*"'/'"doMainPack = .TRUE."'/g' data.ctrl
    else
      cp -f ${optimdir}/ecco_ctrl_MIT_CE_000.opt${optimext} ./
      sed -i -e 's/'"doinitxx = .*"'/'"doinitxx = .FALSE."'/g' data.ctrl
      sed -i -e 's/'"doMainUnpack = .*"'/'"doMainUnpack = .TRUE."'/g' data.ctrl
      sed -i -e 's/'"doMainPack = .*"'/'"doMainPack = .TRUE."'/g' data.ctrl
    fi
        
    #--- 7. executable --------
    \rm -f mitgcmuv*
    cp -f ${builddir}/mitgcmuv${forwadj}_${snx}x${sny}x${nprocs} ./mitgcmuv${forwadj}
    cp -f ${builddir}/tamc.h ./
    cp -f ${builddir}/Makefile .
    
    #--- 8. pickups -----------
    #NOTE: for pickup: copy instead of link to prevent accidental over-write
    \rm -f pickup*
    pickupdir=$scratchdir/pickups_dt1200
    if [[ ${pickupts0} ]]; then
      cp -f ${pickupdir}/pickup${extpickup}.${pickupts1200}.data ./pickup.${pickupts1200}.data
      cp -f ${pickupdir}/pickup${extpickup}.${pickupts1200}.meta ./pickup.${pickupts1200}.meta
      cp -f ${pickupdir}/pickup_seaice${extpickup}.${pickupts1200}.data ./pickup_seaice.${pickupts1200}.data
      cp -f ${pickupdir}/pickup_seaice${extpickup}.${pickupts1200}.meta ./pickup_seaice.${pickupts1200}.meta
    fi
    
    #--- 9. make a list of all linked files ------
    
    \rm -f command_ln_input
    ls -l input_* > command_ln_input
    ls -l input*/input_* >> command_ln_input
    
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
    
    #--- 11. run ----------------------------------
    
    #module load remora
    set -x
    date > run.MITGCM.timing
    mpiexec -n ${nprocs} ${workdir}/mitgcmuv${forwadj}
    date >> run.MITGCM.timing

    #mkdir /work/08381/goldberg/ls6/aste_270x450x180/$rundir/iter${optimext}
    #cp -r profiles /work/08381/goldberg/ls6/aste_270x450x180/$rundir/iter${optimext}
    
    ##clean up
    rm w2*
    rm -r tapes
#    find . -type f -name "STDOUT.*" ! -name "STDOUT.0000" -exec rm {} \;

    #--- 13. OPTIM ---------------------------------
    run_optim $iter $iterprev $costfactor $optimext $workdir $dir_iter $dir_iter_prev $optimdir $itermax $coldstart
    let iter=iter+1
done
  
echo "DONE"

#rm w2* *.bin tile* smooth* get*.m jra55 wu* input_*
#mkdir NAMELISTS ADXXfiles STDs
#mv STDOUT* STDs/
#mv STDERR* STDs
#mv data* NAMELISTS
#mv eedata NAMELISTS
#mv xx* ADXXfiles
#tar czvf OUTPUT_dump.tgz Eta.* logdiffkr* Kap* PH* S.* T.* U.* V.* W.*
#rm Eta.* logdiffkr* Kap* PH* S.* T.* U.* V.* W.*
#tar_command_grid
#rm_command_grid
#tar czvf NAMELISTS.tgz NAMELISTS
#tar czvf ADXXfiles.tgz ADXXfiles
#tar czvf STDs.tgz STDs/
#mv STDs/*.0000 .
#rm -rf STDs
#
#chmod a-wx *.tgz
#
#mkdir diags/STATE diags/TRSP diags/BUDG
#mv diags/state* diags/STATE/
#mv diags/trsp* diags/TRSP
#mv diags/exf* diags/BUDG
#
#cd diags
#tar czvf state_2d_set1.tgz STATE/state_2d_set1.*
#tar czvf state_3d_set1.tgz STATE/state_3d_set1.*
#tar czvf trsp_3d_set1.tgz TRSP/trsp_3d_set1.*
#tar czvf exf_zflux_set1.tgz BUGD/exf_zflux_set1.*
