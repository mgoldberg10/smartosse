CBOP
C     !ROUTINE: tamc.h
C     !INTERFACE:
C     #include "tamc.h"

C     !DESCRIPTION:
C     *================================================================*
C     | tamc.h
C     | o Header file defining parameters and variables for the use of
C     |   the Tangent Linear and Adjoint Model Compiler (TAMC)
C     |   or the Transformations in Fortran tool (TAF).
C     |
C     | started: Christian Eckert eckert@mit.edu  04-Feb-1999
C     | changed: Patrick Heimbach heimbach@mit.edu 06-Jun-2000
C     | cleanup: Martin Losch Martin.Losch@awi.de Nov-2022
C     *================================================================*
CEOP
#ifdef ALLOW_AUTODIFF_TAMC

C     TAMC checkpointing parameters:
C     ==============================
C
C     The checkpointing parameters have to be consistent with other model
C     parameters and variables. This has to be checked before the model is
C     run.
C

#ifdef ALLOW_TAMC_CHECKPOINTING

C     nchklev_1 :: length of inner loop (=size of storage in memory)
C     nchklev_2 :: length of second loop (stored on disk)
C     nchklev_3 :: length of outer loop of 3-level checkpointing
      INTEGER    nchklev_1
      INTEGER    nchklev_2
      INTEGER    nchklev_3
#ifdef AUTODIFF_4_LEVEL_CHECKPOINT
C     nchklev_4 :: length of outer loop of 4-level checkpointing
      INTEGER    nchklev_4
#endif

C--   Note always check for the correct sizes of the common blocks!
C     The product of the nchklev_X needs to be at least equal to
C     nTimeSteps.

C-- calculate numbers below as follows:
c-- take ivy-bridge as example, 3.GB/node -> nchklev_1=24
c-- then take nchklev_[2,3]=sqrt(nTimesteps / 24), round UP
C==== 5 years ------------------------------------------
c change to this for 5-yr run: 2.4GB/node for neh
c      parameter( nchklev_1      =  20 )
c      parameter( nchklev_2      =  84 )
c      parameter( nchklev_3      =  84 )
c change to this for 5-yr run: 2.7GB/node for ivybridge
c      parameter( nchklev_1      =  22 )
c      parameter( nchklev_2      =  80 )
c      parameter( nchklev_3      =  80 )
c change to this for 5-yr run: 3.GB/node for ivybridge
C      parameter( nchklev_1      =  24 )
C      parameter( nchklev_2      =  77 )
C      parameter( nchklev_3      =  77 )
cC==== 6mo, 181days ------------------------------------------
c      parameter( nchklev_1      =  24 )
c      parameter( nchklev_2      =  365 )
c      parameter( nchklev_3      =  1 )
C==== 20 years ------------------------------------------
c change to this for 20-yr run: 2.4GB/node for neh
c      parameter( nchklev_1      =  20 )
c      parameter( nchklev_2      =  163 )
c      parameter( nchklev_3      =  163 )
c change to this for 20-yr run: 2.7GB/node for ivybridge
c      parameter( nchklev_1      =  22 )
c      parameter( nchklev_2      =  155 )
c      parameter( nchklev_3      =  155 )
c change to this for 20-yr run: 3.GB/node for ivybridge
c      parameter( nchklev_1      =  24 )
c      parameter( nchklev_2      =  148 )
c      parameter( nchklev_3      =  148 )
c change to this for 15-yr run: 3.GB/node for ivybridge
c      parameter( nchklev_1      =  24 )
c      parameter( nchklev_2      =  129 )
c      parameter( nchklev_3      =  129 )
c change to this for 25-yr run: 3.GB/node for ivybridge
c      parameter( nchklev_1      =  24 )
c      parameter( nchklev_2      =  166 )
c      parameter( nchklev_3      =  166 )
c Haswell 20-yr run: limit 5.GB/core, 3.2percent or 4.0g per core
c      parameter( nchklev_1      =  52 )
c      parameter( nchklev_2      =  88 )
c      parameter( nchklev_3      =  88 )
c Haswell 1992/01/01 to 2014/12/31 run: limit 5.GB/core, 3.2percent or 4.0g per core
c      parameter( nchklev_1      =  52 )
c      parameter( nchklev_2      =  110 )
c      parameter( nchklev_3      =  110 )
c Haswell 2002/01/01 to 2017/12/31 run: limit 5.GB/core, 3.2percent or 4.0g per core
c Haswell 2002/01/01 to 2019/12/31 run: limit 5.GB/core, 3.2percent or 4.0g per core
c      parameter( nchklev_1      =  52 )
c      parameter( nchklev_2      =  200 )
c      parameter( nchklev_3      =  200 )
c try something using nchklev=20 for 2002-2020
c      parameter( nchklev_1      =  20 )
c      parameter( nchklev_2      =  224 )
c      parameter( nchklev_3      =  224 )
c try something using nchklev=20 for 2002-2024
      parameter( nchklev_1      =  20 )
      parameter( nchklev_2      =  248 )
      parameter( nchklev_3      =  248 )
c  change to these values for very short test runs:
cph      parameter( nchklev_1      =  24 )
cph      parameter( nchklev_2      =  4 )
cph      parameter( nchklev_3      =  3 )
cC Stampede2 SKX 1992/01/01 to 2014/12/31 run: limit 4.GB/core, ?.0g per core, 800GB tapes
c      parameter( nchklev_1      =  6 )
c      parameter( nchklev_2      =  326 )
c      parameter( nchklev_3      =  326 )
C Stampede2 SKX 1992/01/01 to 2014/12/31 run: limit 4.GB/core, ?.0g per core, 422GB tapes, 74GB free
C      parameter( nchklev_1      =  24 )
C      parameter( nchklev_2      =  166 )
C      parameter( nchklev_3      =  166 )
C Stampede2 SKX 1992/01/01 to 2014/12/31 run: limit 4.GB/core, ?.0g per core, 351G tapes
c      parameter( nchklev_1      =  32 )
c      parameter( nchklev_2      =  144 )
c      parameter( nchklev_3      =  144 )
C Stampede2 SKX 1992/01/01 to 2014/12/31 run: limit 4.GB/core, ?.0g per core, 321G tapes
c      parameter( nchklev_1      =  40 )
c      parameter( nchklev_2      =  129 )
c      parameter( nchklev_3      =  129 )
C Stampede2 SKX 1992/01/01 to 2014/12/31 run: limit 4.GB/core, ?.0g per core
c      parameter( nchklev_1      =  44 )
c      parameter( nchklev_2      =  123 )
c      parameter( nchklev_3      =  123 )
C Stampede2 SKX 1992/01/01 to 2014/12/31 run: limit 4.GB/core, ?.0g per core, 422GB tapes, 74GB free
C      parameter( nchklev_1      =  24 )
C      parameter( nchklev_2      =  40000 )
C      parameter( nchklev_3      =  1 )
c--   Note always check for the correct sizes of the common blocks!

#else /* ALLOW_TAMC_CHECKPOINTING undefined */

C     Without ALLOW_TAMC_CHECKPOINTING, nchklev_1 needs to be at least
C     equal to nTimeSteps. This (arbitrary) setting would accommodate a
C     short run (e.g., 10.d with deltaT=10.mn)
      INTEGER    nchklev_1
      PARAMETER( nchklev_1 = 1500 )

#endif /* ALLOW_TAMC_CHECKPOINTING */

C     TAMC keys:
C     ==========
C
C     The keys are used for storing and reading data of the reference
C     trajectory. Currently there is only one global key.
C     ikey_dynamics :: key for main time stepping loop

      COMMON /TAMC_KEYS_I/ ikey_dynamics
      INTEGER ikey_dynamics

C     isbyte :: precision of tapes (both memory and disk).
C               For smaller tapes replace 8 by 4.
      INTEGER    isbyte
      PARAMETER( isbyte    = 4 )

C     maxpass :: maximum number of (active + passive) tracers
C                Note: defined in PTRACERS_SIZE.h if compiling pkg/ptracers
#ifndef ALLOW_PTRACERS
      INTEGER    maxpass
      PARAMETER( maxpass   = 6 )
#endif
C     maxcube :: for Multi-Dim advection, max number of horizontal directions
      INTEGER    maxcube
      PARAMETER( maxcube   = 3 )

#ifdef ALLOW_CG2D_NSA
C     Parameter that is needed for the tape complev_cg2d_iter
C     cannot be smaller than the allowed number of iterations in cg2d
C     (numItersMax >= cg2dMaxIters in data-file)
      INTEGER numItersMax
      PARAMETER ( numItersMax = 200 )
#endif

#endif /* ALLOW_AUTODIFF_TAMC */
C     ================================================================
C     END OF HEADER TAMC
C     ================================================================
