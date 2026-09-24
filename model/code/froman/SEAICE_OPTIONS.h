#ifndef SEAICE_OPTIONS_H
#define SEAICE_OPTIONS_H
#include "PACKAGES_CONFIG.h"
#include "CPP_OPTIONS.h"

C     *==========================================================*
C     | SEAICE_OPTIONS.h
C     | o CPP options file for sea ice package.
C     *==========================================================*
C     | Use this file for selecting options within the sea ice
C     | package.
C     *==========================================================*

#ifdef ALLOW_SEAICE
C---  Package-specific Options & Macros go here

C--   Write "text-plots" of certain fields in STDOUT for debugging.
#undef SEAICE_DEBUG

C--   Allow sea-ice dynamic code.
C     This option is provided to allow use of TAMC
C     on the thermodynamics component of the code only.
C     Sea-ice dynamics can also be turned off at runtime
C     using variable SEAICEuseDYNAMICS.
#define SEAICE_ALLOW_DYNAMICS

C--   By default, the sea-ice package uses its own integrated bulk
C     formulae to compute fluxes (fu, fv, EmPmR, Qnet, and Qsw) over
C     open-ocean.  When this flag is set, these variables are computed
C     in a separate external package, for example, pkg/exf, and then
C     modified for sea-ice effects by pkg/seaice.
#define SEAICE_EXTERNAL_FLUXES

C--   This CPP flag has been retired.  The number of ice categories
C     used to solve for seaice flux is now specified by run-time
C     parameter SEAICE_multDim.
C     Note: be aware of pickup_seaice.* compatibility issues when
C     restarting a simulation with a different number of categories.
c#define SEAICE_MULTICATEGORY

catn: grouping together flags that are likely not used/defined:
catn: These two flags are old ways to modify physics in adj mode in
catn  seaice_growth. Now that we use _adx code, these should not be
catn  set, as we should bypass calling seaice_growth (and call adx)
catn  altogether .  Alternatively, if we are calling seaice_growth
catn  we should be in fw mode only, where these flags dont apply.
#undef SEAICE_MODIFY_GROWTH_ADJ
#undef SEAICE_SIMPLIFY_GROWTH_ADJ 

catn the group of flags below are not relevant for adx code
catn including itd, anything to do with sublimation or grease
C--   run with sea Ice Thickness Distribution (ITD);
C     set number of categories (nITD) in SEAICE_SIZE.h
#undef SEAICE_ITD

C--   Since the missing sublimation term is now included
C     this flag is needed for backward compatibility
#undef SEAICE_DISABLE_SUBLIM

catn This flag is appropriate only if we use seaice_growth.F,
catn and is not part of adx code.
#define SEAICE_ADD_SUBLIMATION_TO_FWBUDGET

catn In the main branch, SIaaflux is perserved for ifdef block
catn SEAICE_DISABLE_HEATCONSFIX, such that when NOT defined (ifndef), a
catn missing heat term associated with treatment of advective heat flux
catn by ocean to ice water exchange (at 0decC) is accounted for.
catn SIaaflux is only valid for ifndef SEAICE_DISABLE_HEATCONSFIX and
catn filled when SEAICEheatConsFix=.true. at runtime. This set of flags
catn (compiled and runtime) do not exist in adx code.
C--   Suspected missing term in coupled ocn-ice heat budget (to be confirmed)
#undef SEAICE_DISABLE_HEATCONSFIX

C--   When set cap the sublimation latent heat flux in solve4temp according
C     to the available amount of ice+snow. Otherwise this term is treated
C     like all of the others -- residuals heat and fw stocks are passed to
C     the ocean at the end of seaice_growth in a conservative manner.
C     SEAICE_CAP_SUBLIM is not needed as of now, but kept just in case.
catn undef cap_sublim in c67w stable run
#undef SEAICE_CAP_SUBLIM

catn Below two flags are retired, now replaced with runtime param
catn SEAICE_doOpenWaterGrowth/Melt
cph#define SEAICE_DO_OPEN_WATER_MELT
cph#define SEAICE_DO_OPEN_WATER_GROWTH
catn: Below flag is retired, replaced with runtime param
catn  SEAICE_areaLoss(Melt)Formula.EQ.1
cph#define FENTY_AREA_EXPANSION_CONTRACTION

C--   Default is constant seaice salinity (SEAICE_salt0); Define the following
C     flag to consider (space & time) variable salinity: advected and forming
C     seaice with a fraction (=SEAICE_saltFrac) of freezing seawater salinity.
C- Note: SItracer also offers an alternative way to handle variable salinity.
C-- must turn off variable_salinity if using seaice_sal0, else budget NOT closed
#undef SEAICE_VARIABLE_SALINITY

C--   Tracers of ice and/or ice cover.
#undef ALLOW_SITRACER
#ifdef ALLOW_SITRACER
C--   To try avoid 'spontaneous generation' of tracer maxima by advdiff.
# define ALLOW_SITRACER_ADVCAP
#endif

C--   Enable grease ice parameterization
C     The grease ice parameterization delays formation of solid
C     sea ice from frazil ice by a time constant and provides a
C     dynamic calculation of the initial solid sea ice thickness
C     HO as a function of winds, currents and available grease ice
C     volume. Grease ice does not significantly reduce heat loss
C     from the ocean in winter and area covered by grease is thus
C     handled like open water.
C     (For details see Smedsrud and Martin, 2014, Ann.Glac.)
C     Set SItrName(1) = 'grease' in namelist SEAICE_PARM03 in data.seaice
C     then output SItr01 is SItrNameLong(1) = 'grease ice volume fraction',
C     with SItrUnit(1) = '[0-1]', which needs to be multiplied by SIheff
C     to yield grease ice volume. Additionally, the actual grease ice
C     layer thickness (diagnostic SIgrsLT) can be saved.
catn this physics is only in seaice_growth, not in adx code
#undef SEAICE_GREASE
C--   Tracers of ice and/or ice cover.
#ifdef SEAICE_GREASE
C     SEAICE_GREASE code requires to define ALLOW_SITRACER
# define ALLOW_SITRACER
#else
# undef ALLOW_SITRACER
#endif
#ifdef ALLOW_SITRACER
C-    To try avoid 'spontaneous generation' of tracer maxima by advdiff.
# define ALLOW_SITRACER_ADVCAP

C-    Include code to diagnose sea ice tracer budgets in
C     seaice_advdiff.F and seaice_tracer_phys.F. Diagnostics are
C     computed the "call diagnostics_fill" statement is commented out.
# undef ALLOW_SITRACER_DEBUG_DIAG
#endif /* ALLOW_SITRACER */

C--   Historically, the seaice model was discretized on a B-Grid. This
C     discretization should still work but it is not longer actively tested
C     and supported. The following flag should always be set in order to use
C     the operational C-grid discretization.
#define SEAICE_CGRID

#ifdef SEAICE_CGRID
C--   Options for the C-grid version only:

C     enable advection of sea ice momentum
catn: this allow_mom_adv is undef by default and has been undef
catn in c67w stable run. it exists only if allow_jfnk or allow_evp
catn or inside allow_lsr (our case, but we donot use it in c67w)
# undef SEAICE_ALLOW_MOM_ADVECTION

C     enable JFNK code by defining the following flag
# undef SEAICE_ALLOW_JFNK

C     enable Krylov code by defining the following flag
catn every undef below were also default undef in stable run of c67w
# undef SEAICE_ALLOW_KRYLOV

C--   Use a different order when mapping 2D velocity arrays to 1D vector
C     before passing it to FGMRES.
# undef SEAICE_JFNK_MAP_REORDER

C     to reproduce old verification results for JFNK
# undef SEAICE_PRECOND_EXTRA_EXCHANGE

C     enable LSR to use global (multi-tile) tri-diagonal solver
catn the 3diag_solver below must be undef in adjoint
# undef SEAICE_GLOBAL_3DIAG_SOLVER

C     enable EVP code by defining the following flag
# undef SEAICE_ALLOW_EVP
# ifdef SEAICE_ALLOW_EVP
C-    When set use SEAICE_zetaMin and SEAICE_evpDampC to limit viscosities
C     from below and above in seaice_evp: not necessary, and not recommended
#  undef SEAICE_ALLOW_CLIPZETA

C     Include code to avoid underflows in EVP-code (copied from CICE).
C     Many compilers can handle this more efficiently with the help of a flag.
#  undef SEAICE_EVP_ELIMINATE_UNDERFLOWS

C     Include code to print residual of EVP iteration for debugging/diagnostics
#  undef ALLOW_SEAICE_EVP_RESIDUAL
# endif /* SEAICE_ALLOW_EVP */

C     smooth regularization (without max-function) of delta for
C     better differentiability
# undef SEAICE_DELTA_SMOOTHREG

C     regularize zeta to zmax with a smooth tanh-function instead
C     of a min(zeta,zmax). This improves convergence of iterative
C     solvers (Lemieux and Tremblay 2009, JGR). No effect on EVP
# undef SEAICE_ZETA_SMOOTHREG

C--   Different yield curves within the VP rheology framework
C     allow the truncated ellipse rheology (runtime flag SEAICEuseTEM)
# undef SEAICE_ALLOW_TEM

C     allow the use of the Mohr Coulomb rheology (runtime flag SEAICEuseMCS)
C     as defined in (Ip 1991) /!\ This is known to give unstable results,
C     use with caution
catn the mcs, mce, and teardrop are new compared to c67w, should be undef
# undef SEAICE_ALLOW_MCS

C     allow the use of Mohr Coulomb with elliptical plastic potential
C     (runtime flag SEAICEuseMCE)
# undef SEAICE_ALLOW_MCE

C     allow the teardrop and parabolic lens  rheology
C     (runtime flag SEAICEuseTD and SEAICEusePL)
# undef SEAICE_ALLOW_TEARDROP

C--   LSR solver settings
C     Use LSR vector code; not useful on non-vector machines, because it
C     slows down convergence considerably, but the extra iterations are
C     more than made up by the much faster code on vector machines. For
C     the only regularly test vector machine these flags a specified
C     in the build options file SUPER-UX_SX-8_sxf90_awi, so that we comment
C     them out here.
# undef SEAICE_VECTORIZE_LSR

C     Use zebra-method (alternate lines) for line-successive-relaxation
C     This modification improves the convergence of the vector code
C     dramatically, so that is may actually be useful in general, but
C     that needs to be tested. Can be used without vectorization options.
catn Martin comment: enable seaice_lsr_zebra  to 
catn avoid recomp related to tridiagu and tridiagv. However, it appear that
catn in my stable c67w run i had these undef, so if they are the cause
catn of unstable adjoint we will revert back to undef. Alternatively,
catn we should recompile c67w with these two defined and see if stable.
catn lsr_zebra is ok, remove recomp
# define SEAICE_LSR_ZEBRA
C     Include code to print residual of nonlinear outer loop of LSR
# undef SEAICE_ALLOW_CHECK_LSR_CONVERGENCE

catn Martin original suggestion to enable seaice_lsr_adjoint_iter.
catn lsr_adjoint_iter is not ok, adjoint blows up. the question perhaps
catn is that why we are using lsr in adjoint? should we switch off dyn
catn in adjoint mode already? and is this the storage of the fw dyn?
# undef SEAICE_LSR_ADJOINT_ITER

C     Use parameterisation of grounding ice for a better representation
C     of fastice in shallow seas
catn allow bottomdrag is undef in c67w stable run
# undef SEAICE_ALLOW_BOTTOMDRAG
C======================= BELOW IS IRRELEVANT for CGRID============
#else /* not SEAICE_CGRID, but old B-grid */
C--   Options for the B-grid version only:

C-    By default for B-grid dynamics solver wind stress under sea-ice is
C     set to the same value as it would be if there was no sea-ice.
C     Define following CPP flag for B-grid ice-ocean stress coupling.
# define SEAICE_BICE_STRESS
catn: this flag below has now been replaced by the bice_stress flag just above
c#undef SEAICE_TEST_ICE_STRESS_1

C-    By default for B-grid dynamics solver surface tilt is obtained
C     indirectly via geostrophic velocities. Define following CPP
C     in order to use ETAN instead.
# define EXPLICIT_SSH_SLOPE

C-    Defining this flag turns on FV-discretization of the B-grid LSOR solver.
C     It is smoother and includes all metric terms, similar to C-grid solvers.
C     It is here for completeness, but its usefulness is unclear.
# undef SEAICE_LSRBNEW

#endif /* SEAICE_CGRID */
C======================= ABOVE IS IRRELEVANT for CGRID============

C--   Some regularisations
C-    When set limit the Ice-Loading to mass of 1/5 of Surface ocean grid-box
catn this cap_iceload is undef in c67w stable run
#undef SEAICE_CAP_ICELOAD

C-    When set use SEAICE_clipVelocties = .true., to clip U/VICE at 40cm/s,
C     not recommended
#undef SEAICE_ALLOW_CLIPVELS

C--   Seaice flooding
catn: no such ifdef exist, need to use runtime param SEAICEuseFlooding
catn#define ALLOW_SEAICE_FLOODING

C-- pkg/seaice cost functions compile flags
c     >>> Sea-ice volume (requires pkg/cost)
C--   Use the adjointable sea-ice thermodynamic model
C     in seaice_growth_adx.F instead of seaice_growth.F
C     This options excludes more complex physics such
C     as sublimation, ITD, and frazil.
c-- this set is for not doing seaice thermo adjoint
#undef SEAICE_USE_GROWTH_ADX
#undef SEAICE_ALLOW_FREEDRIFT

c-- this set is for seaice thermo adjoint
c-- this freedrift flag, note if we turn on seaice thermodynamic adjoint 
c-- define this in order for freedrift to be active in adjoint mode
CCAB will set a runtime flag for free drift, in FW =0 , in ADJ = 1
Catn#define SEAICE_USE_GROWTH_ADX
Catn#define SEAICE_ALLOW_FREEDRIFT

C--   pkg/seaice cost functions compile flags
C-    Sea-ice volume (requires pkg/cost)
#undef ALLOW_COST_ICE
#ifdef ALLOW_COST_ICE
C-    Enable template for sea-ice volume export in seaice_cost_export.F
C     (requires pkg/cost & ALLOW_COST_ICE defined)
# undef ALLOW_SEAICE_COST_EXPORT
#endif /* ALLOW_COST_ICE */

#endif /* ALLOW_SEAICE */
#endif /* SEAICE_OPTIONS_H */

CEH3 ;;; Local Variables: ***
CEH3 ;;; mode:fortran ***
CEH3 ;;; End: ***
