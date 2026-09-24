#***********************************************************************
# Makefile for the off-line large scale optimization with m1qn3
# in reverse communication mode.
#
# started: Martin Losch Martin.Losch@awi.de 24-Apr-2012
#
# changed:
#
#***********************************************************************

MAKEFILE=Makefile
# The optimization routines.
SRC		=	optim_main.F			\
			optim_sub.F			\
			optim_readparms.F		\
			optim_readdata.F		\
			optim_writedata.F		\
			optim_store_m1qn3.F		\
                        m1qn3_offline.F			\
                        ddot.F

EXEDIR     = .

# default suffix for pre-processed fortran files is f
SUFF=f
# for case-insensitive file systems you may need this
# SUFF=for
# Location of cpp preprocessor
# default is (Linux)
CPP             = cat $< | /lib/cpp -P -traditional
# Mac OS X
# CPP             = cat $< | /usr/bin/cpp -P -traditional
# on SUNOS
# CPP		= cat $< | /usr/ccs/lib/cpp

#MAKEDEPEND=makedepend
# this works when you done have a makedepend
MAKEDEPEND=../../MITgcm_c68v/tools/xmakedepend

INCLUDEDIRS     = -I.				\
                  -I../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/

LIBDIRS         =
LIBS            =

EXECUTABLE      = $(EXEDIR)/optim.x

# The cpp flags.
CPPFLAGS = -DREAL_BYTE=4		\
	-DMAX_INDEPEND=300000000        \
	-D_RL='double precision'	\
	-D_RS='double precision'	\
	-D_d='d'

#                -DMAX_INDEPEND=293570968        \
# FORTRAN compiler and its flags.
# It is important that byte conversion flags are consistent between this
# compilation and the mitgcmuv compilation
# default is gfortran
FC              = gfortran
FFLAGS          =  -fconvert=big-endian -mcmodel=large

# ifort compilers
#FC              = ifort
#FFLAGS          = -mieee-fp -132 -r8 -i4 -W0 -WB -CB -fpe0 -traceback -convert big_endian -assume byterecl

# SGI o3k IRIX64
#FC              = f77
#FFLAGS          = -extend_source -bytereclen -mips4 -r8 -static

# AER cluster
#FC		= /opt/mpich/bin/mpif77
#FFLAGS		= -byteswapio -r8 -Mnodclchk -Mextend

# Cray compiler
#FC     = ftn
#FFLAGS =  -h byteswapio -hnoomp -O0 -hfp0

SMALLF      = $(SRC:.F=.$(SUFF))
OBJECTS     = $(SRC:.F=.o)

.SUFFIXES:
.SUFFIXES: .o .$(SUFF) .F

all: small_f $(EXECUTABLE)
$(EXECUTABLE): $(OBJECTS)
	$(FC) -o $@ $(FFLAGS) $(OBJECTS) $(LIBDIRS) $(LIBS)

small_f: $(SMALLF)

depend:
	$(MAKEDEPEND) -o .$(SUFF) $(INCLUDEDIRS) $(SRC)

# The normal chain of rules is (  .F - .f - .o  )
.F.for:
	$(CPP) $(CPPFLAGS) $(INCLUDEDIRS) > $@
.for.o:
	$(FC) $(FFLAGS) -c $<
.F.f:
	$(CPP) $(CPPFLAGS) $(INCLUDEDIRS) > $@
.f.o:
	$(FC) $(FFLAGS) -c $<

# Cleaning options.
clean:
	-rm -f *.o *.f *.for

Clean:
	@make -f $(MAKEFILE) clean
	-rm -f OPWARM.*

CLEAN:
	@make -f $(MAKEFILE) Clean
	-rm -f $(EXECUTABLE)

# DO NOT DELETE


ddot.f: /usr/include/stdc-predef.h
m1qn3_offline.f: m1qn3a_common.h m1qn3_common.h mlis3_common.h
m1qn3_offline.f: /usr/include/stdc-predef.h
optim_main.f: /usr/include/stdc-predef.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEMACROS.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEOPTIONS.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_OPTIONS.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_OPTIONS.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_SIZE.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/EEPARAMS.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/PACKAGES_CONFIG.h
optim_readdata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/SIZE.h
optim_readdata.f: optim.h /usr/include/stdc-predef.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEMACROS.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEOPTIONS.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_OPTIONS.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_OPTIONS.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_SIZE.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/EEPARAMS.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/PACKAGES_CONFIG.h
optim_readparms.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/SIZE.h
optim_readparms.f: optim.h /usr/include/stdc-predef.h
optim_store_m1qn3.f: m1qn3a_common.h m1qn3_common.h mlis3_common.h
optim_store_m1qn3.f: /usr/include/stdc-predef.h
optim_sub.f: m1qn3_common.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEMACROS.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEOPTIONS.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_OPTIONS.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_OPTIONS.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_SIZE.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/EEPARAMS.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/PACKAGES_CONFIG.h
optim_sub.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/SIZE.h
optim_sub.f: optim.h /usr/include/stdc-predef.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEMACROS.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_EEOPTIONS.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CPP_OPTIONS.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_OPTIONS.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/CTRL_SIZE.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/EEPARAMS.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/PACKAGES_CONFIG.h
optim_writedata.f: ../../MITgcm_c68v/mysetups/aste_270x450x180/osses/build_phibot/SIZE.h
optim_writedata.f: optim.h /usr/include/stdc-predef.h
