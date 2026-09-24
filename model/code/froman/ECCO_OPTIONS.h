#ifndef ECCO_OPTIONS_H
#define ECCO_OPTIONS_H
#include "PACKAGES_CONFIG.h"
#include "CPP_OPTIONS.h"

CBOP
C !ROUTINE: ECCO_OPTIONS.h
C !INTERFACE:
C #include "ECCO_OPTIONS.h"

C !DESCRIPTION:
C *==================================================================*
C | CPP options file for ECCO (ecco) package:
C | Control which optional features to compile in this package code.
C *==================================================================*
CEOP

#ifdef ALLOW_ECCO
#ifdef ECCO_CPPOPTIONS_H

C-- When multi-package option-file ECCO_CPPOPTIONS.h is used (directly included
C    in CPP_OPTIONS.h), this option file is left empty since all options that
C   are specific to this package are assumed to be set in ECCO_CPPOPTIONS.h

#else /* ndef ECCO_CPPOPTIONS_H */

C-- Package-specific Options & Macros go here

C       >>> ALLOW_GENCOST_CONTRIBUTION: interactive way to add basic 2D cost function terms.
C       > In data.ecco, this requires the specification of data file (name, frequency,
C         etc.), bar file name for corresp. model average, standard error file name, etc.
C       > In addition, adding such cost terms requires editing ecco_cost.h to increase
C         NGENCOST, and editing cost_gencost_customize.F to implement the actual
C         model average (i.e. the bar file content).
#define ALLOW_GENCOST_CONTRIBUTION
C       >>> free form version of GENCOST: allows one to use otherwise defined elements (e.g.
C         psbar and and topex data) while taking advantage of the cost function/namelist slots
C         that can be made available using ALLOW_GENCOST_CONTRIBUTION. To this end
C         ALLOW_GENCOST_CONTRIBUTION simply switches off tests that check whether all of the
C         gencost elements (e.g. gencost_barfile and gencost_datafile) are specified in data.ecco.
C       > While this option increases flexibility within the gencost framework, it implies more room
C         for error, so it should be used cautiously, and with good knowledge of the rest of pkg/ecco.
C       > It requires providing a specific cost function routine, and editing cost_gencost_all.F accordingly.
C       >>> 3 dimensional version of GENCOST:
#define ALLOW_GENCOST3D
C   Note regarding GENCOST usage:
C   > In data.ecco, this requires the specification of data file (name,
C     frequency, etc.), bar file name for corresp. model average, standard
C     error file name, etc.
C   > In addition, adding such cost terms requires editing ECCO_SIZE.h to
C     increase NGENCOST/NGENCOST3D, and editing cost_gencost_customize.F to
C     implement the actual model average (i.e. the bar file content).
# undef ALLOW_GENCOST_1D
# undef ALLOW_GENCOST_SSTV4_OUTPUT

C o Allow Open-Boundary cost contributions
#ifdef ALLOW_OBCS
C   Open-Boundary cost is meaningless without compiling pkg/obcs
C   Note: Make sure that coresponding OBCS N/S/W/E Option is defined
# undef ALLOW_OBCSN_COST_CONTRIBUTION
# undef ALLOW_OBCSS_COST_CONTRIBUTION
# undef ALLOW_OBCSW_COST_CONTRIBUTION
# undef ALLOW_OBCSE_COST_CONTRIBUTION
#  undef OBCS_AGEOS_COST_CONTRIBUTION
#  undef OBCS_VOLFLUX_COST_CONTRIBUTION
#  undef BAROTROPIC_OBVEL_CONTROL
#endif /* ALLOW_OBCS */

C o Set ALLOW_OBCS_COST_CONTRIBUTION (Do not edit/modify):
#if (defined (ALLOW_OBCSN_COST_CONTRIBUTION) || \
     defined (ALLOW_OBCSS_COST_CONTRIBUTION) || \
     defined (ALLOW_OBCSW_COST_CONTRIBUTION) || \
     defined (ALLOW_OBCSE_COST_CONTRIBUTION))
# define ALLOW_OBCS_COST_CONTRIBUTION
#endif

C o Use total time-varying volume to weight contributions, if defined
#undef ECCO_VARIABLE_AREAVOLGLOB
#undef ALLOW_GENCOST_TRANSPORT
#undef ALLOW_GENCOST_SIGMAR
#undef ALLOW_GENCOST_DTHETADR

C o Include global mean steric sea level correction
#undef ALLOW_PSBAR_STERIC
#ifdef ATMOSPHERIC_LOADING
C   Apply inverse barometer correction (coded within ATMOSPHERIC_LOADING)
# undef ALLOW_IB_CORR
#endif

C o Allow for near-shore and high-latitude altimetry
#undef ALLOW_SHALLOW_ALTIMETRY
#undef ALLOW_HIGHLAT_ALTIMETRY

C o Allow for In-Situ Profiles cost function contribution
#define ALLOW_PROFILES_CONTRIBUTION

C o Cost function output format
#define ALLOW_ECCO_OLD_FC_PRINT

C o Generate more text in STDOUT
#undef ECCO_VERBOSE
#undef ALLOW_ECCO_DEBUG

C-- partially retired options (i.e., only used to set default switch):
# undef ALLOW_SSH_COST_CONTRIBUTION
# undef ALLOW_SST_COST_CONTRIBUTION
# undef ALLOW_SEAICE_COST_CONTRIBUTION

C   ==================================================================
#endif /* ndef ECCO_CPPOPTIONS_H */
#endif /* ALLOW_ECCO */
#endif /* ECCO_OPTIONS_H */
