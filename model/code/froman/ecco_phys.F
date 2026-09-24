#include "ECCO_OPTIONS.h"
#ifdef ALLOW_SHELFICE
# include "SHELFICE_OPTIONS.h"
#endif
#ifdef ALLOW_AUTODIFF
# include "AUTODIFF_OPTIONS.h"
#endif
#ifdef ALLOW_SEAICE
# include "SEAICE_OPTIONS.h"
#endif

C---+----1----+----2----+----3----+----4----+----5----+----6----+----7-|--+----|
CBOP
C     !ROUTINE: ECCO_PHYS

C     !INTERFACE:
      SUBROUTINE ECCO_PHYS( myTime, myIter, myThid )

C     !DESCRIPTION:
C     Compute some derived quantities and averages
C     for GenCost and ECCO cost function.

C     !USES:
      IMPLICIT NONE
c     == global variables ==
#include "EEPARAMS.h"
#include "SIZE.h"
#include "PARAMS.h"
#include "GRID.h"
#include "DYNVARS.h"
#include "FFIELDS.h"
#ifdef ALLOW_ECCO
# include "ECCO_SIZE.h"
# include "ECCO.h"
#endif
#ifdef ALLOW_PTRACERS
# include "PTRACERS_SIZE.h"
# include "PTRACERS_FIELDS.h"
#endif
#if (defined ALLOW_GENCOST_CONTRIBUTION) && (defined ALLOW_SHELFICE)
# include "SHELFICE.h"
#endif
#ifdef ALLOW_AUTODIFF_TAMC
# include "tamc.h"
#endif
#ifdef ALLOW_SEAICE
# include "SEAICE_SIZE.h"
# include "SEAICE_PARAMS.h"
# include "SEAICE.h"
#endif

C     !INPUT PARAMETERS:
C     myTime    :: Current time in simulation
C     myIter    :: Current time-step number
C     myThid    :: my Thread Id number
      _RL     myTime
      INTEGER myIter, myThid

C     !LOCAL VARIABLES:
C     bi, bj    :: tile indices
C     i, j, k   :: loop indices
      INTEGER bi, bj
      INTEGER i, j, k
#ifdef ALLOW_GENCOST_CONTRIBUTION
      INTEGER kgen, kgen3d, itr
      _RL areavolTile(nSx,nSy), areavolGlob
      _RL tmpfld, tmpvol, tmpmsk, tmpmsk2, tmpmskW, tmpmskS
      _RL tmp_sigmsk, tmpsig, tmpsig_lower, tmpsig_upper
      _RL tmpfluxS, tmpfluxW 
c here add local vars for full horflux (from code written by Nora Loose) 
c localT      ::  local copy of tracer field to compute gmredi transport
c tmp2dmskW   ::  copy of cell area mask to compute gmredi transports
c tmp2dmskS   ::  copy of cell area mask to compute gmredi transports
c tmp3dmskW   ::  copy of section mask
c tmp3dmskS   ::  copy of section mask
c trIdentity  ::  =1 for theta, =2 for salt
c diffKh      ::  =diffKhT for theta, = diffKhS for salt
c df[x,y]     ::  field of diffusive fluxes
      integer trIdentity
      _RL diffKh
      _RL localT  (1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
      _RL tmp2dmskW  (1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL tmp2dmskS  (1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL tmp3dmskW  (1:sNx,1:sNy,Nr)
      _RL tmp3dmskS  (1:sNx,1:sNy,Nr)
      _RL dfx  (1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL dfy  (1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      integer ktrsp
#ifdef ALLOW_GENCOST_DTHETADR
      integer k1,k2,i1(nr),j1(nr),bi1(nr),bj1(nr),kdthetadr
      integer icount,nstep
      _RL dthetadr, dthetaL, dthetaR, xC0, yC0, zC0, ss
      _RL Tcutoff,lonline,latlower,latupper
#endif
#ifdef ALLOW_GENCOST_SIGMAR
      _RL rhoKp1  (1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL rhoKm1  (1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL sigmaX  (1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
      _RL sigmaY  (1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
      _RL sigmaR  (1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
#endif
#endif

C- note: defined with overlap here, not needed, but more efficient
      _RL trVolW, trVolS, trHeatW, trHeatS, trSaltW, trSaltS
c      _RL trVolW(1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
c      _RL trVolS(1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
c      _RL trHeatW(1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
c      _RL trHeatS(1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
c      _RL trSaltW(1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)
c      _RL trSaltS(1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr)

      _RL tmpfac
      _RL sIceLoadFacLoc
      _RL T_ref,S_ref,temp,r_S_ref
#ifdef ATMOSPHERIC_LOADING
#ifdef ALLOW_IB_CORR
      _RL ploadbar, AREAsumGlob, PLOADsumGlob
      _RL AREAsumTile(nSx,nSy), PLOADsumTile(nSx,nSy)
      _RL m_eta_ib(1-OLx:sNx+OLx,1-OLy:sNy+OLy,nSx,nSy)
      _RL sterht  (1-OLx:sNx+OLx,1-OLy:sNy+OLy,nSx,nSy)
#endif
#endif
      _RL rhoLoc(1-OLx:sNx+OLx,1-OLy:sNy+OLy,Nr,nSx,nSy)
#ifdef ALLOW_PSBAR_STERIC
      _RL VOLsumTile(nSx,nSy), RHOsumTile(nSx,nSy)
      _RL VOLsumGlob_1, RHOsumGlob_1
c     CHARACTER*(MAX_LEN_MBUF) msgBuf
#endif
C     Mload     :: total mass load (kg/m**2)
c     _RL Mload(1-OLx:sNx+OLx,1-OLy:sNy+OLy,nSx,nSy)
#if ( defined ALLOW_AUTODIFF_TAMC && defined ALLOW_GENCOST_CONTRIBUTION )
C     ikey   :: tape key (depends on kgen)
      INTEGER ikey
#endif
CEOP

      T_ref = -1.9 _d 0
      S_ref = 34.8 _d 0
      IF ( S_ref .ne. 0. _d 0 ) THEN
        r_S_ref=1. _d 0 / S_ref
      ELSE
        r_S_ref = 0. _d 0
      ENDIF
cHP adding Nora's changeset for implementing full horflux cost 
catn initialize diffKh to avoid recomp
      diffKh = 0. _d 0

      tmpfac = recip_rhoConst*recip_gravity
      sIceLoadFacLoc = zeroRL
      IF ( useRealFreshWaterFlux ) sIceLoadFacLoc = recip_rhoConst

      DO bj=myByLo(myThid),myByHi(myThid) !{{{ [bibj0]
       DO bi=myBxLo(myThid),myBxHi(myThid)
        IF ( myIter .EQ. -1 ) THEN
          DO k = 1,Nr
            CALL FIND_RHO_2D(
     I                1-OLx, sNx+OLx, 1-OLy, sNy+OLy, k,
     I                theta(1-OLx,1-OLy,k,bi,bj),
     I                salt (1-OLx,1-OLy,k,bi,bj),
     O                rhoLoc(1-OLx,1-OLy,k,bi,bj),
     I                k, bi, bj, myThid )
          ENDDO !k
        ELSE    !myIter
          DO k = 1,Nr
           DO j=1-OLy,sNy+OLy
            DO i=1-OLx,sNx+OLx
              rhoLoc(i,j,k,bi,bj) = rhoInSitu(i,j,k,bi,bj)
            ENDDO
           ENDDO
          ENDDO !k
        ENDIF !myIter
       ENDDO !bi
      ENDDO !bj                          !}}} [bibj0]

#ifdef ALLOW_PSBAR_STERIC
      DO bj=myByLo(myThid),myByHi(myThid) !{{{ [bibj1]
       DO bi=myBxLo(myThid),myBxHi(myThid)
        RHOsumTile(bi,bj) = 0. _d 0
        VOLsumTile(bi,bj) = 0. _d 0
        DO k = 1,Nr
         DO j = 1,sNy
          DO i =  1,sNx
           RHOsumTile(bi,bj) = RHOsumTile(bi,bj)
     &          + ( rhoConst + rhoLoc(i,j,k,bi,bj) )
     &           *hFacC(i,j,k,bi,bj)*drF(k)*rA(i,j,bi,bj)
           VOLsumTile(bi,bj) = VOLsumTile(bi,bj)
     &          + hFacC(i,j,k,bi,bj)*drF(k)*rA(i,j,bi,bj)
          ENDDO
         ENDDO
        ENDDO
       ENDDO
      ENDDO                                !}}}[bibj1]
      CALL GLOBAL_SUM_TILE_RL( VOLsumTile, VOLsumGlob_1, myThid )
      CALL GLOBAL_SUM_TILE_RL( RHOsumTile, RHOsumGlob_1, myThid )

# ifndef ALLOW_AUTODIFF
      _BEGIN_MASTER(myThid)
# endif
      VOLsumGlob = VOLsumGlob_1
      RHOsumGlob = RHOsumGlob_1/VOLsumGlob

      IF (RHOsumGlob_0.GT.0. _d 0) THEN
        sterGloH = VOLsumGlob_0/globalArea
     &        *(1. _d 0 - RHOsumGlob/RHOsumGlob_0)
      ELSE
        sterGloH = 0. _d 0
      ENDIF

c     WRITE(msgBuf,'(A,1PE21.14)') ' sterGloH= ', sterGloH
c     CALL PRINT_MESSAGE( msgBuf, standardMessageUnit,
c    &                       SQUEEZE_RIGHT, myThid )
# ifndef ALLOW_AUTODIFF
      _END_MASTER(myThid)
      _BARRIER
# endif

#endif /* ALLOW_PSBAR_STERIC */

#ifdef ATMOSPHERIC_LOADING
#ifdef ALLOW_IB_CORR
      DO bj=myByLo(myThid),myByHi(myThid) !{{{ [bibj2]
       DO bi=myBxLo(myThid),myBxHi(myThid)
        PLOADsumTile(bi,bj) = 0. _d 0
        AREAsumTile(bi,bj) = 0. _d 0
        DO j = 1,sNy
         DO i =  1,sNx
          PLOADsumTile(bi,bj) = PLOADsumTile(bi,bj)
     &          + pLoad(i,j,bi,bj)
     &           *maskC(i,j,1,bi,bj)*rA(i,j,bi,bj)
          AREAsumTile(bi,bj) = AREAsumTile(bi,bj)
     &          + maskC(i,j,1,bi,bj)*rA(i,j,bi,bj)
         ENDDO
        ENDDO
       ENDDO
      ENDDO                               !}}}[bibj2]
      CALL GLOBAL_SUM_TILE_RL( AREAsumTile, AREAsumGlob, myThid )
      CALL GLOBAL_SUM_TILE_RL( PLOADsumTile, PLOADsumGlob, myThid )
      ploadbar = PLOADsumGlob/AREAsumGlob
#endif /* ALLOW_IB_CORR */
#endif /* ATMOSPHERIC_LOADING */

      DO bj=myByLo(myThid),myByHi(myThid)        !{{{ [bibj3]
       DO bi=myBxLo(myThid),myBxHi(myThid)
        DO j = 1-OLy, sNy+OLy
         DO i = 1-OLx, sNx+OLx

C calculate total sea level including inverse barometer (IB) effect if
C  there is air pressure forcing
           m_eta(i,j,bi,bj) =
     &           ( etaN(i,j,bi,bj)
     &           + sIceLoad(i,j,bi,bj)*sIceLoadFacLoc
#ifdef ALLOW_PSBAR_STERIC
C apply Greatbatch correction
     &           + sterGloH
#endif /* ALLOW_PSBAR_STERIC */
     &           ) * maskC(i,j,1,bi,bj)

C Model equivalent of ocean bottom pressure gauge data (in m^2/s^2)
C  that are NOT corrected for global ocean mean atmospheric pressure variations
C  = Ocean mass + sea-ice & snow load + air-pressure load + Greatbatch corr.
C  (all terms on RHS are converted to m^2/s^2). It is
C  essentially Mload (as in pkg/sbo/sbo_calc.F) plus air-pressure load
           m_bp(i,j,bi,bj) =
     &           ( etaN(i,j,bi,bj)
c    &           + Ro_surf(i,j,bi.bj)
     &           - R_low(i,j,bi,bj)
#ifdef ALLOW_PSBAR_STERIC
C add back the correction due to the global mean steric ssh change,
C     i.e. sterGloH computed above (units converted from m to m2/s2)
     &           + sterGloH
#endif /* ALLOW_PSBAR_STERIC */
     &           ) * gravity
C sIceLoad in kg/m^2
     &         + sIceLoad(i,j,bi,bj) * gravity * sIceLoadFacLoc
C pLoad in N/m^2
     &         + pLoad(i,j,bi,bj) * recip_rhoConst
         ENDDO
        ENDDO
C integrate rho_anomaly through water column
        DO k = 1, Nr
         DO j = 1-OLy, sNy+OLy
          DO i = 1-OLx, sNx+OLx
           m_bp(i,j,bi,bj) = m_bp(i,j,bi,bj)
     &         + rhoLoc(i,j,k,bi,bj)*drF(k)*hFacC(i,j,k,bi,bj)
     &                              * gravity * recip_rhoConst
          ENDDO
         ENDDO
        ENDDO
        DO j = 1-OLy, sNy+OLy
         DO i = 1-OLx, sNx+OLx
           m_bp(i,j,bi,bj) = m_bp(i,j,bi,bj) * maskC(i,j,1,bi,bj)
         ENDDO
        ENDDO

#ifdef ATMOSPHERIC_LOADING
#ifdef ALLOW_IB_CORR
        DO j = 1-OLy, sNy+OLy
         DO i = 1-OLx, sNx+OLx
C calculate IB correction m_eta_ib (in m)
           m_eta_ib(i,j,bi,bj) =
     &           ( ploadbar - pLoad(i,j,bi,bj) )*tmpfac
     &           * maskC(i,j,1,bi,bj)
C calculte dynamic sea level for comparison with altimetry data (in m)
           m_eta_dyn(i,j,bi,bj) =
     &           ( m_eta(i,j,bi,bj) - m_eta_ib(i,j,bi,bj) )
     &           * maskC(i,j,1,bi,bj)

C calculate GRACE-equvivalent ocean bottom pressure (in m2/s2)
C  by removing global ocean mean atmospheric pressure variations
           m_bp_nopabar(i,j,bi,bj) =
     &           ( m_bp(i,j,bi,bj)
     &           - ploadbar * recip_rhoConst
     &           ) * maskC(i,j,1,bi,bj)
C calculate steric height
C (in m; = m_eta_dyn - (m_bp_nopabr * recip_gravity + R_low))
C R_low (<0) is Depth in m.
           sterht(i,j,bi,bj) = m_eta_dyn(i,j,bi,bj)
     &          - ( m_bp_nopabar(i,j,bi,bj) * recip_gravity
c    &            - Ro_surf(i,j,bi,bj)
     &            + R_low(i,j,bi,bj)  )
         ENDDO
        ENDDO
#endif /* ALLOW_IB_CORR */
#endif /* ATMOSPHERIC_LOADING */
       ENDDO
      ENDDO                             !!}}}[bibj3]

#ifdef ALLOW_DIAGNOSTICS
      IF ( useDiagnostics .AND. myIter.GE.0 ) THEN  !{{{
        CALL DIAGNOSTICS_FILL( m_eta, 'SSHNOIBC', 0,1, 0,1,1, myThid )
        CALL DIAGNOSTICS_SCALE_FILL( m_bp, recip_gravity, 1,
     &                         'OBPGMAP ', 0,1, 0,1,1, myThid )
#ifdef ATMOSPHERIC_LOADING
#ifdef ALLOW_IB_CORR
        CALL DIAGNOSTICS_FILL( m_eta_ib,
     &                         'SSHIBC  ', 0,1, 0,1,1, myThid )
        CALL DIAGNOSTICS_FILL( m_eta_dyn,
     &                         'SSH     ', 0,1, 0,1,1, myThid )
        CALL DIAGNOSTICS_FILL( sterht,
     &                         'STERICHT', 0,1, 0,1,1, myThid )
        CALL DIAGNOSTICS_SCALE_FILL( m_bp_nopabar, recip_gravity, 1,
     &                         'OBP     ', 0,1, 0,1,1, myThid )
#endif /* ALLOW_IB_CORR */
#endif /* ATMOSPHERIC_LOADING */
      ENDIF                                         !}}}
#endif /* ALLOW_DIAGNOSTICS */

      DO bj=myByLo(myThid),myByHi(myThid)
       DO bi=myBxLo(myThid),myBxHi(myThid)
        DO k = 1,Nr
         DO j = 1-OLy,sNy+OLy
          DO i = 1-OLx,sNx+OLx
           m_UE(i,j,k,bi,bj) = 0. _d 0
           m_VN(i,j,k,bi,bj) = 0. _d 0
          ENDDO
         ENDDO
        ENDDO
       ENDDO
      ENDDO

      CALL ROTATE_UV2EN_RL(
     U          uVel, vVel, m_UE, m_VN,
     I          .TRUE., .TRUE., .FALSE., Nr, myThid )

c--   trVol : volume flux    --- [m^3/sec] (order of 10^6 = 1 Sv)
c--   trHeat: heat transport --- [Watt] (order of 1.E15 = PW)
c--   trSalt: salt transport --- [kg/sec] (order 1.E9 equiv. 1 Sv in vol.)
c--       convert from [ppt*m^3/sec] via rhoConst/1000.
c--       ( 1ppt = 1000*[mass(salt)]/[mass(seawater)] )

c-- init
      CALL ECCO_ZERO( trVol,  Nr, zeroRL, myThid )
      CALL ECCO_ZERO( trHeat, Nr, zeroRL, myThid )
      CALL ECCO_ZERO( trSalt, Nr, zeroRL, myThid )

#ifdef ALLOW_GENCOST_CONTRIBUTION

C---+----1----+----2----+----3----+----4----+----5----+----6----+----7-|--+----|
#ifdef ALLOW_GENCOST_SIGMAR
c copy from do_oceanc_phys.F        !{{{ [sigmaR]
      DO bj=myByLo(myThid),myByHi(myThid)
       DO bi=myBxLo(myThid),myBxHi(myThid)

        DO k=1,Nr
         DO j=1-OLy,sNy+OLy
          DO i=1-OLx,sNx+OLx
C This is currently used by GMRedi, IVDC, MXL-depth  and Diagnostics
           sigmaX(i,j,k) = 0. _d 0
           sigmaY(i,j,k) = 0. _d 0
           sigmaR(i,j,k) = 0. _d 0
          ENDDO
         ENDDO
        ENDDO

        DO j=1-OLy,sNy+OLy
         DO i=1-OLx,sNx+OLx
          rhoKm1 (i,j)   = 0. _d 0
          rhoKp1 (i,j)   = 0. _d 0
         ENDDO
        ENDDO

c------ k loop in reverse
        DO k=Nr,1,-1
         IF (k.GT.1) THEN
                   CALL FIND_RHO_2D(
     I                 1-OLx, sNx+OLx, 1-OLy, sNy+OLy, k,
     I                 theta(1-OLx,1-OLy,k-1,bi,bj),
     I                 salt (1-OLx,1-OLy,k-1,bi,bj),
     O                 rhoKm1,
     I                 k-1, bi, bj, myThid )
         ENDIF
         DO j=1-OLy,sNy+OLy
          DO i=1-OLx,sNx+OLx
           rhoKp1(i,j) = rhoInSitu(i,j,k,bi,bj)
          ENDDO !i
         ENDDO  !j
         CALL GRAD_SIGMA(
     I          bi, bj, 1-OLx, sNx+OLx, 1-OLy, sNy+OLy, k,
     I          rhoInSitu(1-OLx,1-OLy,k,bi,bj), rhoKm1, rhoKp1,
     O          sigmaX, sigmaY, sigmaR,
     I          myThid )

         DO j=1-OLy,sNy+OLy
          DO i=1-OLx,sNx+OLx
           sigmaRfield(i,j,k,bi,bj)=sigmaR(i,j,k)
          ENDDO  !i
         ENDDO   !j
        ENDDO    !k
c--- done k loop
       ENDDO    !bi
      ENDDO     !bj                 %!}}} [sigmaR]
#endif /* ALLOW_GENCOST_SIGMAR */

C---+----1----+----2----+----3----+----4----+----5----+----6----+----7-|--+----|
#ifdef ALLOW_GENCOST_DTHETADR
      kdthetadr=0                       !{{{ [dthetadr]
      DO kgen=1,NGENCOST
        IF (gencost_barfile(kgen)(1:18).EQ.'m_boxmean_dthetadr') THEN
          Tcutoff  = gencost_preproc_r(1,kgen)
          lonline  = gencost_preproc_r(2,kgen)
          latlower = gencost_preproc_r(3,kgen)
          latupper = gencost_preproc_r(4,kgen)
          k1=gencost_preproc_i(1,kgen)
          k2=gencost_preproc_i(2,kgen)
          kdthetadr = kgen
        ENDIF
      ENDDO

      IF(kdthetadr .GT. 0) THEN
       DO k=1,nr
        bi1(k)=0
        bj1(k)=0
        i1(k)=0
        j1(k)=0
       ENDDO
       dthetadr=0. _d 0
       DO bj=myByLo(myThid),myByHi(myThid)
        DO bi=myBxLo(myThid),myBxHi(myThid)
         DO j=2,sNy-1
          DO i=2,sNx-1
c- cant tell at the moment if this is along i or j, assume i for now
           IF((abs(xc(i,j,bi,bj)-(lonline)).LT. 0.001 _d 0) .AND.
     &            (yc(i,j,bi,bj).GT. latlower  .AND. 
     &             yc(i,j,bi,bj).LT. latupper)) THEN
            dthetaL = 0. _d 0
            dthetaR = 0. _d 0
            DO k=k1,k2
 
             IF((hFacC(i-1,j,k  ,bi,bj).GT.0.9 _d 0 .AND.
     &           hFacC(i  ,j,k  ,bi,bj).GT.0.9 _d 0      ).AND.
     &          (hFacC(i-1,j,k+1,bi,bj).GT.0.9 _d 0 .AND.
     &           hFacC(i  ,j,k+1,bi,bj).GT.0.9 _d 0      )) THEN
 
              dthetaL=theta(i-1,j,k  ,bi,bj)-Tcutoff
              dthetaR=theta(i  ,j,k  ,bi,bj)-Tcutoff
 
              IF (dthetaL.LT.0. _d 0 .AND. dthetaR.GE.0. _d 0) THEN
                 bi1(k) = bi
                 bj1(k) = bj
                 i1(k)  = i
                 j1(k)  = j
              ENDIF
             ENDIF  !hFacC=1.0
            ENDDO !k=k1,k2
           ENDIF
          ENDDO   !i
         ENDDO    !j
        ENDDO     !bi
       ENDDO      !bj
 
c-- now compute gradient d distance dz

c-- dthetadr: the slope in m_hor/m_ver of the isothermal line Tcutoff
       dthetadr = 0. _d 0
       icount   = 0
       DO k=k1,k2
        IF(   (bi1(k).GT.0.AND.bi1(k+1).GT.0)
     &   .AND.(bj1(k).GT.0.AND.bj1(k+1).GT.0) ) THEN

         ss=1. _d 0
         nstep = 1
c         xC0 = 0. _d 0
c         yC0 = 0. _d 0
         zC0 = 0. _d 0
         i=i1(k)
         j=j1(k)
         bi=bi1(k)
         bj=bj1(k)

c- note overestimate the slope by 1 grid point
c- because vertical slope is infinite (dz/dx) or zero (dx/dz)
         IF(i1(k).LE.i1(k+1)) THEN
c          do i=i1(k),i1(k+1),nstep
c           xC0 = xC0 + dxC(i,j,bi,bj)*ss
c          enddo
          zC0 = zC0 + drC(k+1)
          icount = icount + 1
          dthetaR = theta(i,j,k+1,bi,bj)-theta(i,j,k,bi,bj)
c          dthetadr = dthetadr + ss*SQRT(xC0*xC0+yC0*yC0)/zC0
          dthetadr = dthetadr + dthetaR/zC0
         ENDIF
        ENDIF
       ENDDO
       IF(icount .GT. 0) dthetadr = dthetadr / icount

      ENDIF!kdthetadr               !}}} [dthetadr]
#endif /* ALLOW_GENCOST_DTHETADR */

C---+----1----+----2----+----3----+----4----+----5----+----6----+----7-|--+----|
#ifdef ALLOW_GENCOST_TRANSPORT
catn: trVol cost, separated from others
      DO kgen=1,NGENCOST              !{{{ trVol 
       ktrsp=0
       IF ( gencost_msk_is3d(kgen) ) THEN
        IF (gencost_barfile(kgen)(1:4).EQ.'m_tr') THEN
         ktrsp = gencost_msk_pointer3d(kgen)
        ENDIF
       ENDIF
      ENDDO

catn: initialize for taf
      trVolW =0. _d 0
      trVolS =0. _d 0
      trHeatW=0. _d 0
      trHeatS=0. _d 0
      trSaltW=0. _d 0
      trSaltS=0. _d 0
      tmpmskW=0. _d 0
      tmpmskS=0. _d 0

      IF ( ktrsp .GT. 0 ) THEN
       DO bj=myByLo(myThid),myByHi(myThid)
        DO bi=myBxLo(myThid),myBxHi(myThid)
         DO k = 1,Nr
          DO j = 1,sNy
           DO i =  1,sNx
            trVolW  = 0. _d 0
            trVolS  = 0. _d 0
            trHeatW = 0. _d 0
            trHeatS = 0. _d 0
            trSaltW = 0. _d 0
            trSaltS = 0. _d 0
            temp    = 0. _d 0

c no def msktrVolW, should be gencost_mskW(i,j,k,bi,bj,ktrsp)
c no def msktrVolS, should be gencost_mskS(i,j,k,bi,bj,ktrsp)
            tmpmskW=gencost_mskW(i,j,k,bi,bj,ktrsp)
     &                *hFacW(i,j,k,bi,bj)*dyG(i,j,bi,bj)*drF(k)
            tmpmskS=gencost_mskS(i,j,k,bi,bj,ktrsp)
     &                *hFacS(i,j,k,bi,bj)*dxG(i,j,bi,bj)*drF(k)

c maskInW & maskInS are likely what are read in from data.ecco
cVolume
            trVolW = uVel(i,j,k,bi,bj)*tmpmskW*maskInW(i,j,bi,bj)
            trVolS = vVel(i,j,k,bi,bj)*tmpmskS*maskInS(i,j,bi,bj)
cHeat
            temp=(theta(i,j,k,bi,bj)+theta(i-1,j,k,bi,bj))*halfRL-T_ref
            IF ( temp.GE. 0. _d 0 )
     &       trHeatW = trVolW*temp*HeatCapacity_Cp*rhoConst

            temp=(theta(i,j,k,bi,bj)+theta(i,j-1,k,bi,bj))*halfRL-T_ref
            IF ( temp.GE. 0. _d 0 )
     &       trHeatS = trVolS*temp*HeatCapacity_Cp*rhoConst
cFW
            temp = oneRL - ((salt(i,j,k,bi,bj)+salt(i-1,j,k,bi,bj))
     &                *halfRL)/S_ref
            IF ( temp.GE. 0. _d 0 ) trSaltW=trVolW*temp*rhoConst/1000.

            temp = oneRL - ((salt(i,j,k,bi,bj)+salt(i,j-1,k,bi,bj))
     &                *halfRL)/S_ref
            IF ( temp.GE. 0. _d 0 ) trSaltS=trVolS*temp*rhoConst/1000.

c now suming
            trVol(i,j,k,bi,bj)  = trVolW  + trVolS
            trHeat(i,j,k,bi,bj) = trHeatW + trHeatS
            trSalt(i,j,k,bi,bj) = trSaltW + trSaltS
               
           ENDDO !k
          ENDDO  !j
         ENDDO   !i
        ENDDO    !bj
       ENDDO     !bi
      ENDIF      !ktrsp               !}}} [trVol]
#endif /* ALLOW_GENCOST_TRANSPORT */

cts ---
c First: Fill the following SCALAR masks & weights for each (i,j,k,bi,bj) grid cell
c   tmpvol - 3D cell volume
c   tmpmsk - mask for the gencost_barfile field (e.g. theta)
c            Either: expand from 2D mask gencost_mskCsurf across nonzero
c            entries of gencost_mskVertical (Nr x NGENCOST array)
c            or
c            copy from 3D mask gencost_mskC
cts ---
      DO kgen=1,NGENCOST

       itr = gencost_itracer(kgen)

catn init to avoid recomp
       diffKh = 0. _d 0

       CALL ECCO_ZERO( gencost_storefld(1-OLx,1-OLy,1,1,kgen),
     &                 1, zeroRL, myThid )

       DO bj=myByLo(myThid),myByHi(myThid)
        DO bi=myBxLo(myThid),myBxHi(myThid)
         areavolTile(bi,bj)=0. _d 0
        ENDDO
       ENDDO
       areavolGlob=0. _d 0

cHP adding Nora's changeset for implementing full horflux cost 
       IF (gencost_barfile(kgen)(1:15).EQ.'m_horflux_theta') THEN
        trIdentity = 1
        diffKh = diffKhT
       ELSEIF (gencost_barfile(kgen)(1:14).EQ.'m_horflux_salt' .OR.
     &         gencost_barfile(kgen)(1:14).EQ.'m_horflux_fwEu') THEN
        trIdentity = 2
        diffKh = diffKhS
       ELSE
        diffKh = 0. _d 0
       ENDIF

C---+----1----+----2----+----3----+----4----+----5----+----6----+----7-|--+----|
       DO bj=myByLo(myThid),myByHi(myThid)     !{{{ [bibj4]
        DO bi=myBxLo(myThid),myBxHi(myThid)
         DO j = 1-OLy,sNy+OLy
          DO i =  1-OLx,sNx+OLx
           DO k = 1,Nr
             tmp3dmskW(i,j,k)=0. _d 0
             tmp3dmskS(i,j,k)=0. _d 0
             localT(i,j,k)=0. _d 0
           ENDDO
          ENDDO
         ENDDO

         DO j = 1,sNy                 !{{{ [jloop]
          DO i =  1,sNx
c---------
           DO k = 1,Nr!{{{ [kloop1]
            tmpvol=hFacC(i,j,k,bi,bj)*drF(k)*rA(i,j,bi,bj)

            tmpmsk=0. _d 0
            IF (.NOT.gencost_msk_is3d(kgen)) THEN
             tmpmsk=gencost_mskCsurf(i,j,bi,bj,kgen)*
     &              gencost_mskVertical(k,kgen)
#ifdef ALLOW_GENCOST3D
            ELSE
             kgen3d=gencost_msk_pointer3d(kgen)
             tmpmsk=gencost_mskC(i,j,k,bi,bj,kgen3d)
#endif /* ALLOW_GENCOST3D */
            ENDIF

C ---- If density mask is enabled, use it here ----
            IF ( maskC(i,j,k,bi,bj).EQ.oneRS .AND.
     &           gencost_useDensityMask(kgen) ) THEN
C            - first, calculate the scalar density
             CALL FIND_RHO_SCALAR(
     I              theta(i,j,k,bi,bj),
     I              salt(i,j,k,bi,bj),
     I              gencost_refPressure(kgen),
     O              tmpsig,
     I              myThid )
C            - subtract 1000 to get sigma
             tmpsig = tmpsig - 1000. _d 0
C            - now, tmpmsk is sigmoid times this value
             tmpsig_lower = 0.5 + 0.5*tanh(gencost_tanhScale(kgen)
     &           *(tmpsig-gencost_sigmaLow(kgen)))
             tmpsig_upper = 0.5 - 0.5*tanh(gencost_tanhScale(kgen)
     &           *(tmpsig-gencost_sigmaHigh(kgen)))
C             - update mask value based on the sigmoid function
             tmp_sigmsk = tmpsig_lower*tmpsig_upper
             tmpmsk = tmpmsk*tmp_sigmsk
            ENDIF
C ---- end of density mask (but tmpmsk is used below)

cts ---
c Now: at each (i,j,k,bi,bj) fill the SCALAR variables
c   tmpfld - from 3D field theta, salt, ptracer
c            or
c            from 2D field with eta, shelfice
c
c   tmpmsk2 - 1 or 0 weighting for areavolTile
cts ---
            tmpfld=0. _d 0
            tmpmsk2=0. _d 0
            IF (gencost_barfile(kgen)(1:15).EQ.'m_boxmean_theta') THEN
             tmpfld=theta(i,j,k,bi,bj)
             IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
            ELSEIF (gencost_barfile(kgen)(1:14).EQ.'m_boxmean_salt')
     &        THEN
             tmpfld=salt(i,j,k,bi,bj)
             IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
            ELSEIF (gencost_barfile(kgen)(1:13).EQ.'m_boxmean_vol') THEN
             tmpfld=1. _d 0
             IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
#ifdef ALLOW_PTRACERS
            ELSEIF (gencost_barfile(kgen)(1:17).EQ.'m_boxmean_ptracer')
     &        THEN
             tmpfld=pTracer(i,j,k,bi,bj,itr)
             IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
#endif /* ALLOW_PTRACERS */
            ENDIF

            IF (gencost_barfile(kgen)(1:14).EQ.'m_boxcont_heat') THEN
              tmpfld=theta(i,j,k,bi,bj)*HeatCapacity_Cp*rhoConst 
              IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
            ELSEIF (gencost_barfile(kgen)(1:14).EQ.'m_boxcont_salt')
     &        THEN
              tmpfld=salt(i,j,k,bi,bj)*rhoConst/1000.
              IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
            ELSEIF (gencost_barfile(kgen)(1:12).EQ.'m_boxcont_fw') THEN
catn implemented here
              tmpfld=1. _d 0 -(salt(i,j,k,bi,bj)*r_S_ref)
              IF (tmpfld.LE. 0. _d 0) tmpfld = 0. _d 0
              IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
catn: note the sigmar and dthetadr will need testing.  working ok
c on c65q but not yet tested on later checkpoints
#ifdef ALLOW_GENCOST_SIGMAR
            ELSEIF (gencost_barfile(kgen)(1:16).EQ.'m_boxmean_sigmaR')
     &        THEN
              tmpfld=sigmaRfield(i,j,k,bi,bj)
              IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
#endif /* ALLOW_GENCOST_SIGMAR */
            ENDIF

cts ---
c Fill 3D field
c       gencost_store - masked field of interest * grid cell volume
c                       note: this accumulates along z dim
c
c Fill tile field (1 val per tile)
c       areavolTile - volume of each tile, this gets summed to a global
c                     value
cts ---
            gencost_storefld(i,j,bi,bj,kgen) =
     &          gencost_storefld(i,j,bi,bj,kgen)
     &          +tmpmsk*tmpfld*tmpvol
            areavolTile(bi,bj)=areavolTile(bi,bj)
#ifdef ECCO_VARIABLE_AREAVOLGLOB
     &          +tmpmsk2*tmpvol
#else
     &          +tmpmsk2*eccoVol_0(i,j,k,bi,bj)
#endif

           ENDDO ! Ends do k=1,Nr       !}}}
                                                 !{{{
           tmpmsk  = 0. _d 0
           tmpfld  = 0. _d 0
           tmpmsk2 = 0. _d 0
           IF (gencost_barfile(kgen)(1:13).EQ.'m_boxmean_eta') THEN
            tmpmsk=maskC(i,j,1,bi,bj)*gencost_mskCsurf(i,j,bi,bj,kgen)
            tmpfld = m_eta(i,j,bi,bj)
#if (defined ATMOSPHERIC_LOADING) && (defined ALLOW_IB_CORR)
            IF (gencost_barfile(kgen)(1:17).EQ.'m_boxmean_eta_dyn') THEN
             tmpfld = m_eta_dyn(i,j,bi,bj)
            ENDIF
#endif
            IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
           ENDIF

#ifdef ALLOW_SEAICE
           IF (gencost_barfile(kgen)(1:14).EQ.'m_boxmean_area') THEN
            tmpmsk=maskC(i,j,1,bi,bj)*gencost_mskCsurf(i,j,bi,bj,kgen)
            tmpfld=area(i,j,bi,bj)
            IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
           ELSEIF (gencost_barfile(kgen)(1:14).EQ.'m_boxmean_heff') THEN
            tmpmsk=maskC(i,j,1,bi,bj)*gencost_mskCsurf(i,j,bi,bj,kgen)
            tmpfld=heff(i,j,bi,bj)
            IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
#endif /* ALLOW_SEAICE */
           ENDIF
                                                  !}}}
#ifdef ALLOW_SHELFICE
cts ---                                       !{{{
c Shelfice:
c   Simply accumulate shelfice FWF or HF into tmpfld here
c   This will fill gencost_storefld with this value *rA
c   For FreshWaterFlux
c           gencost_storefld = shelficefreshwaterflux / rho * rA
c                            = [kg/m^2/s] / [kg/m^3] * [m^2]
c                            = [m^3/s]
c
c   For heatflux
c           gencost_storefld = shelficeheatflux * rA
c                            = [W/m^2] *[m^2]
c                            = [W]
cts ---
           IF((gencost_barfile(kgen)(1:16).EQ.'m_boxmean_shifwf').OR.
     &        (gencost_barfile(kgen)(1:16).EQ.'m_boxmean_shihtf')) THEN

            tmpmsk=maskSHI(i,j,1,bi,bj)*
     &             gencost_mskCsurf(i,j,bi,bj,kgen)

            IF (gencost_barfile(kgen)(11:16).EQ.'shifwf') THEN
             tmpfld=shelficeFreshWaterFlux(i,j,bi,bj) / rhoConstFresh
            ELSEIF (gencost_barfile(kgen)(11:16).EQ.'shihtf') THEN
             tmpfld=shelficeHeatFlux(i,j,bi,bj)
            ENDIF
            IF (tmpmsk.NE.0. _d 0) tmpmsk2=1. _d 0
           ENDIF                            !}}}
#endif /* ALLOW_SHELFICE */

cts ---
c Fill 2D field
c   gencost_store - masked field of interest * rA
c
c Fill tile field (1 val per tile)
c       areavolTile - total rA on each tile for mskC != 0
cts ---
           gencost_storefld(i,j,bi,bj,kgen) =
     &        gencost_storefld(i,j,bi,bj,kgen)
     &        +tmpmsk*tmpfld*rA(i,j,bi,bj)
           areavolTile(bi,bj)=areavolTile(bi,bj)
     &        +tmpmsk2*rA(i,j,bi,bj)
c---------
catn moved transport on separate nr block way above
C---+----1----+----2----+----3----+----4----+----5----+----6----+----7-|--+----|
           DO k = 1,Nr                          !{{{ [kloop2]

            tmpmskW=0. _d 0
            tmpmskS=0. _d 0
            tmpfluxS=0. _d 0
            tmpfluxW=0. _d 0
            IF (.NOT.gencost_msk_is3d(kgen)) THEN
              tmpmskW=gencost_mskWsurf(i,j,bi,bj,kgen)
     &          *gencost_mskVertical(k,kgen)
              tmpmskS=gencost_mskSsurf(i,j,bi,bj,kgen)
     &          *gencost_mskVertical(k,kgen)
#ifdef ALLOW_GENCOST3D
            ELSE
              kgen3d=gencost_msk_pointer3d(kgen)
              tmpmskW=gencost_mskW(i,j,k,bi,bj,kgen3d)
              tmpmskS=gencost_mskS(i,j,k,bi,bj,kgen3d)
#endif /* ALLOW_GENCOST3D */
            ENDIF

            IF (
     &        (gencost_barfile(kgen)(1:15).EQ.'m_horflux_theta').OR.
     &        (gencost_barfile(kgen)(1:14).EQ.'m_horflux_salt').OR.
     &        (gencost_barfile(kgen)(1:14).EQ.'m_horflux_fwEu')
     &           ) THEN
c---------- Store local copy of section masks to add diffusive fluxes further down
             tmp3dmskW(i,j,k)=tmpmskW
             tmp3dmskS(i,j,k)=tmpmskS
            ENDIF

            tmpmskW=tmpmskW*hFacW(i,j,k,bi,bj)*dyG(i,j,bi,bj)*drF(k)
            tmpmskS=tmpmskS*hFacS(i,j,k,bi,bj)*dxG(i,j,bi,bj)*drF(k)

            IF (gencost_barfile(kgen)(1:13).EQ.'m_horflux_vol') THEN
              gencost_storefld(i,j,bi,bj,kgen) =
     &          gencost_storefld(i,j,bi,bj,kgen)
     &          +uVel(i,j,k,bi,bj)*tmpmskW
     &          +vVel(i,j,k,bi,bj)*tmpmskS
            ENDIF

            IF (gencost_barfile(kgen)(1:15).EQ.'m_horflux_theta') THEN
              tmpfld=(theta(i,j,k,bi,bj)+theta(i-1,j,k,bi,bj))*halfRL
              IF (gencost_preproc(1,kgen)(1:3).EQ.'ref') THEN
               tmpfld=tmpfld-gencost_preproc_r(1,kgen)
              ENDIF
              tmpfluxW = tmpfld*HeatCapacity_Cp*rhoConst 
              tmpfld=(theta(i,j,k,bi,bj)+theta(i,j-1,k,bi,bj))*halfRL
              tmpfluxS = tmpfld*HeatCapacity_Cp*rhoConst 
              gencost_storefld(i,j,bi,bj,kgen) =
     &          gencost_storefld(i,j,bi,bj,kgen)
     &          +uVel(i,j,k,bi,bj)*tmpmskW*tmpfluxW
     &          +vVel(i,j,k,bi,bj)*tmpmskS*tmpfluxS
            ENDIF

            IF (gencost_barfile(kgen)(1:14).EQ.'m_horflux_salt') THEN
              tmpfld=(salt(i,j,k,bi,bj)+salt(i-1,j,k,bi,bj))*halfRL
              tmpfluxW = tmpfld*rhoConst/1000.0 
              tmpfld=(salt(i,j,k,bi,bj)+salt(i,j-1,k,bi,bj))*halfRL
              tmpfluxS = tmpfld*rhoConst/1000.0 
              gencost_storefld(i,j,bi,bj,kgen) =
     &          gencost_storefld(i,j,bi,bj,kgen)
     &          +uVel(i,j,k,bi,bj)*tmpmskW*tmpfluxW
     &          +vVel(i,j,k,bi,bj)*tmpmskS*tmpfluxS
            ENDIF
C Eu is for Eulerian
            IF (gencost_barfile(kgen)(1:14).EQ.'m_horflux_fwEu') THEN
              tmpfld=1. _d 0 - ((salt(i,j,k,bi,bj)+salt(i-1,j,k,bi,bj))
     &               *halfRL)*r_S_ref
              IF (tmpfld.GE. 0. _d 0) THEN
               tmpfluxW = tmpfld*rhoConst/1000.0 
              ELSE
               tmpfluxW = 0. _d 0
              ENDIF
              tmpfld=1. _d 0 - ((salt(i,j,k,bi,bj)+salt(i,j-1,k,bi,bj))
     &               *halfRL)*r_S_ref
              IF (tmpfld.GE. 0. _d 0) THEN
               tmpfluxS = tmpfld*rhoConst/1000.0 
              ELSE
               tmpfluxS = 0. _d 0
              ENDIF
              gencost_storefld(i,j,bi,bj,kgen) =
     &          gencost_storefld(i,j,bi,bj,kgen)
     &          +uVel(i,j,k,bi,bj)*tmpmskW*tmpfluxW
     &          +vVel(i,j,k,bi,bj)*tmpmskS*tmpfluxS

            ENDIF
C     end k-loop
           ENDDO               !}}} [kloop2]
c---------
catn treat dthetadr on separate block because i have some hardcoded things
#ifdef ALLOW_GENCOST_DTHETADR
           IF (gencost_barfile(kgen)(1:18).EQ.'m_boxmean_dthetadr') THEN
            IF(dthetadr.GT.0 _d 0 .AND. i.EQ.1.AND.j.EQ.1) THEN
             gencost_storefld(i,j,bi,bj,kgen) = 
     &       gencost_storefld(i,j,bi,bj,kgen) + dthetadr
            ELSE
             gencost_storefld(i,j,bi,bj,kgen) = 0. _d 0
            ENDIF
            IF(dthetadr.GT.0 _d 0) THEN
             areavolTile(bi,bj)= 1. _d 0
            ELSE
             areavolTile(bi,bj)= 0. _d 0
            ENDIF
           ENDIF
#endif /* ALLOW_GENCOST_DTHETADR */
c---------
          ENDDO !i
         ENDDO  !j                !}}} [jloop]

C---+----1----+----2----+----3----+----4----+----5----+----6----+----7-|--+----|
c------ Add diffusive and GM/Redi fluxes to horflux_[theta/salt]
         IF (
     &     (gencost_barfile(kgen)(1:15).EQ.'m_horflux_theta').OR.
     &     (gencost_barfile(kgen)(1:14).EQ.'m_horflux_salt')
     &      ) THEN
c--------- Make a local copy of tracer array (for this tile)
c this code is identical to Nora's except that I also compute the
c diffusive and bolus transport wrt a reference temperature/salinity
          IF (gencost_barfile(kgen)(1:15).EQ.'m_horflux_theta') THEN !{{{
           DO k=1,Nr
            DO j=1-OLy,sNy+OLy
             DO i=1-OLx,sNx+OLx
              localT(i,j,k)=theta(i,j,k,bi,bj)-T_ref
             ENDDO
            ENDDO
           ENDDO
          ELSEIF (gencost_barfile(kgen)(1:14).EQ.'m_horflux_salt') THEN
           DO k=1,Nr
            DO j=1-OLy,sNy+OLy
             DO i=1-OLx,sNx+OLx
              localT(i,j,k)=1. _d 0 -(salt(i,j,k,bi,bj)*r_S_ref)
              IF (localT(i,j,k).LE. 0. _d 0) THEN
               localT(i,j,k)= 0. _d 0
              ENDIF
             ENDDO
            ENDDO
           ENDDO
          ENDIF                                                     !}}}
c--------
          DO k=1,Nr           !{{{ [kloop3]
           DO j=1-OLy,sNy+OLy
            DO i=1-OLx,sNx+OLx
             tmp2dmskW(i,j)=hFacW(i,j,k,bi,bj)*dyG(i,j,bi,bj)*drF(k)
             tmp2dmskS(i,j)=hFacS(i,j,k,bi,bj)*dxG(i,j,bi,bj)*drF(k)
catn initialize df[x,y] to avoid recomp
             dfx(i,j) = 0. _d 0
             dfy(i,j) = 0. _d 0
            ENDDO
           ENDDO
c --------- Diffusive flux in X; assume deepFac=1; ignore biharmonic
           IF (diffKh.GT.0.) THEN
            CALL gad_diff_x(
     I       bi,bj,k,tmp2dmskW,diffKh,localT,
     O       dfx,
     I       myThid)
            CALL gad_diff_y(
     I       bi,bj,k,tmp2dmskS,diffKh,localT,
     O       dfy,
     I       myThid)
           ELSE
            DO j=1-OLy,sNy+OLy
             DO i=1-OLx,sNx+OLx
              dfx(i,j) = 0. _d 0
              dfy(i,j) = 0. _d 0
             ENDDO
            ENDDO
           ENDIF
c -----------Add GM/Redi flux in [X,Y] to df[x,y]
c commenting this because still causes problems in adjoint
c#ifdef ALLOW_GMREDI
c           IF ( useGMredi ) THEN
c            CALL gmredi_xtransport(
c     I        trIdentity, bi, bj, k, 1-OLx+1, sNx+OLx, 1-OLy, sNy+OLy,
c     I        tmp2dmskW,localT,
c     U        dfx,
c     I        myThid )
c            CALL gmredi_ytransport(
c     I        trIdentity, bi, bj, k, 1-OLx+1, sNx+OLx, 1-OLy, sNy+OLy,
c     I        tmp2dmskS,localT,
c     U        dfy,
c     I        myThid )
c           ENDIF
c#endif
c-------- Add fluxes in [X,Y] to gencost; assume rhoFacC = 1
           IF (gencost_barfile(kgen)(1:15).EQ.'m_horflux_theta')
     &     THEN
            DO j=1,sNy
             DO i=1,sNx
              gencost_storefld(i,j,bi,bj,kgen) = 
     &         gencost_storefld(i,j,bi,bj,kgen) +
     &         (dfx(i,j)*tmp3dmskW(i,j,k)+dfy(i,j)*tmp3dmskS(i,j,k))
     &         *HeatCapacity_Cp*rhoConst
             ENDDO
            ENDDO
c
           ELSEIF (gencost_barfile(kgen)(1:14).EQ.'m_horflux_salt')
     &     THEN
            DO j=1,sNy
             DO i=1,sNx
              gencost_storefld(i,j,bi,bj,kgen) = 
     &         gencost_storefld(i,j,bi,bj,kgen) +
     &         (dfx(i,j)*tmp3dmskW(i,j,k)+dfy(i,j)*tmp3dmskS(i,j,k))
     &         *rhoConst/1000.
             ENDDO
            ENDDO
           ENDIF

          ENDDO !k           !}}} [kloop3]
c gencost_barfile = m_horflux_[theta,salt]
         ENDIF
c
c----------------- end of Nora's changes for FULL horflux costs
       ENDDO !bi
      ENDDO !bj                             !}}}[bibj4]

cts ---
c Divide all values in gencost_storefld by
c   areavolGlob: scalar representing global volume of
c                quantity of interest.
c
c Note: for shelfice, do not take this final average to make
c       comparable to shelfice_cost_final.
cts ---
       IF ( gencost_barfile(kgen)(1:9).EQ.'m_boxmean' .AND.
     &      gencost_barfile(kgen)(11:13).NE.'shi' .AND.
     &      gencost_barfile(kgen)(11:13).NE.'vol' ) THEN
        CALL GLOBAL_SUM_TILE_RL( areavolTile, areavolGlob, myThid )
#ifdef ALLOW_AUTODIFF_TAMC
C     avoid recomputing areavolGlob multiple times each time this
C     routine is called
        ikey = kgen + (ikey_dynamics-1)*NGENCOST
CADJ STORE areavolGlob = comlev1_ngencost, key = ikey
#endif
        CALL ECCO_DIV( gencost_storefld(1-OLx,1-OLy,1,1,kgen),
     &                 areavolGlob, 1, 1, myThid )
       ENDIF

C     end kgen-loop
      ENDDO

#endif /* ALLOW_GENCOST_CONTRIBUTION */

      RETURN
      END
