#ifndef CTRL_OPTIONS_H
#define CTRL_OPTIONS_H
#include "PACKAGES_CONFIG.h"
#include "CPP_OPTIONS.h"

CBOP
C !ROUTINE: CTRL_OPTIONS.h
C !INTERFACE:
C #include "CTRL_OPTIONS.h"

C !DESCRIPTION:
C *==================================================================*
C | CPP options file for Control (ctrl) package:
C | Control which optional features to compile in this package code.
C *==================================================================*
CEOP

#ifdef ALLOW_CTRL
#ifdef ECCO_CPPOPTIONS_H

C-- When multi-package option-file ECCO_CPPOPTIONS.h is used (directly included
C    in CPP_OPTIONS.h), this option file is left empty since all options that
C   are specific to this package are assumed to be set in ECCO_CPPOPTIONS.h

#else /* ndef ECCO_CPPOPTIONS_H */
C   ==================================================================
C-- Package-specific Options & Macros go here

C o I/O and pack settings
#define CTRL_SET_PREC_32
c the nondim flag below is no longer relevant with gentim[2d,3d] and genarr[2d,3d]
C#undef ALLOW_NONDIMENSIONAL_CONTROL_IO
#define ALLOW_PACKUNPACK_METHOD2

C o sets of controls
#define ALLOW_GENTIM2D_CONTROL
#define ALLOW_GENARR2D_CONTROL
#define ALLOW_GENARR3D_CONTROL

c even with gentim[2d,3d] and genarr[2d,3d],
c flags for bottomdrag, kap[gm,redi], diffkr are still needed
C o bottom drags, genarr2d
#define ALLOW_BOTTOMDRAG_CONTROL
C o kapgm, genarr3d
#define ALLOW_KAPGM_CONTROL
C o kapredi, genarr3d
#define ALLOW_KAPREDI_CONTROL
C o diffkr, genarr3d
#define ALLOW_DIFFKR_CONTROL

C  o Originally the first two time-reccords of control
C    variable tau u and tau v were skipped.
C    The CTRL_SKIP_FIRST_TWO_ATM_REC_ALL option extends this
C    to the other the time variable atmospheric controls.
#undef CTRL_SKIP_FIRST_TWO_ATM_REC_ALL

C  o impose bounds on controls
#define ALLOW_ADCTRLBOUND

C  Note: this flag turns on extra smoothing code in ctrl_get_gen.F which
C  is inconsistent with the Weaver and Courtier, 2001 algorithm, and
C  should probably not be used. The corresponding 3D flag applied only
C  to deprecated code that is now removed. At some point we will remove
C  this flag and associated code as well.
C  o apply pkg/smooth/smooth_diff2d.F to 2D controls (outside of Smooth_Correl2D)
#undef ALLOW_SMOOTH_CTRL2D

C   o rotate u/v vector control to zonal/meridional 
C   components
#define ALLOW_ROTATE_UV_CONTROLS

#undef ALLOW_CTRL_DEBUG

C   ==================================================================
#endif /* ndef ECCO_CPPOPTIONS_H */
#endif /* ALLOW_CTRL */
#endif /* CTRL_OPTIONS_H */
