#!/usr/bin/env python3

import sys
import numpy as np


class c:
    '''
    Constants used for the constant values are those within the scipy.constants module [1], imported
    as c. This allows for calls like c.m_e for electron mass for example.

    Written by Scott Donaldson, V0.1, 25/06/2025

    References
    ----------
    [1] https://docs.scipy.org/doc/scipy/reference/constants.html for full units, but scipy takes
    them from CODATA Recommended Values of the Fundamental Physical Constants 2022.
    '''
    c = 299792458.0
    e = 1.602176634e-19
    R = 8.31446261815324
    k = 1.380649e-23
    m_e = 9.1093837139e-31
    N_A = 6.02214076e+23
    hbar = 1.0545718176461565e-34
    alpha = 0.0072973525643
    hartree = 4.359744722206e-18
    bohr_r = 5.29177210544e-11


def check_unit(to_check):
    """ Check the validity of a given input unit string.

    I.e. to check if this unit is currently implemented in the python library and more specifically
    the `si_to_atomic` function.
    This function checks against a manually created array of strings that must be updated if a unit
    is added to or removed from `si_to_atomic`.

    Parameters
    ----------
    to_check : string
        Unit type string, to be checked against list of valid implemented units.

    Returns
    -------
    Boolean
        True if `to_check` is in the list of valid units, False otherwise.

    Notes
    -----
    Written by Scott Donaldson, V0.1, 14/07/2020
    """

    # List of all valid units, if another unit is added to the function it must be added
    # to this list or the function will give an error when used as si_in input
    si_unit_list = ["bohr","m","cm","nm","a","ang","pm","me","m_e","amu","kg","g","aut","s","ms","mus","ns","ps","fs","e","c","coulomb","d","debye","ha","hartree","mha","ev","mev","ry","mry","j","erg","kj.mol-1","kj/mol","kcal/mol","kcal.mo-1","hz","mhz","thz","ghz","cm-1","k","j/mol/k","jmol-1k-1","ha/bohr","ha.bohr-1","ev/a","ev.a-1","n","dyne","auv","a/ps","a.ps-1","ang/ps","a/fs","a.fs-1","ang/fs","bohr/ps","bohr.ps-1","bohr/ps","bohr/fs","bohr.fs-1","bohr/fs","m/s","m.s-1","ha/bohr**3","ha.bohr-3","hartree/bohr**3","ev/a**3","ev/a**3","ev/a**3","pa","mpa","gpa","tpa","ppa","atm","bar","1/bohr","bohr-1","1/m","m-1","1/nm","nm-1","1/pm","pm-1","1/a","a-1","ha/bohr**2","ha/bohr**2","ev/a**2","ev.a-2","n/m","n.m-1","dyne/cm","dyne.cm-1","bohr**3","m**3","cm**3","nm**3","a**3","pm**3","acu","ampere","acd","amperemetre2","ampere.m2","amfd","tesla","gauss","agr","bohr2","bohr**2","fm2","barn","ha/bohr/e","ha.bohr-1.e-1","ev/a/e","ev/ang/e","n/coulomb","n.coulomb-1","mub","magneton","atom","atomic","kj"]

    # Check to make sure the si_in unit is in the list of valid units si_unit_list
    if to_check.lower() in si_unit_list:
        return True
    else:
        return False


def si_to_atomic(si_in,si_in_val):
    """ Convert from Si units to atomic units.

    Convert from the input float value `si_in_val` from the unit type given in `si_in`
    to dimensionless atomic units.

    This is based on the castep module io.f90, especially its `physical units'.

    The accepted strings for `si_in` are those as used by CASTEP so should not need reformatting
    when passing arguments from a CASTEP file or CASTEP directly.

    If the `si_in` string is not represented currently by a unit conversion then the program will
    exit giving an error.

    Note: If a unit type is added or removed, the string representing it must be added or removed
    from the array in `check_unit`.

    Parameters
    ----------
    si_in : string
        String input value giving units of imput float value `si_in_value` to convert from to
        dimensionless atomic units.
        Unit names must be as defined in CASTEP module io.f90 (i.e. units CASTEP uses). `si_in`
        is case insensitive.
    si_in_val : float
        Value to be converted from the units given as string in si_in to dimensionless atomic units.

    Returns
    -------
    float
        The value si_in_val converted from the units in si_in to dimensionless atomic units.

    Notes
    -----
    Constants used for the constant values are those within the scipy.constants module [1], imported
    as c. This allows for calls like c.m_e for electron mass for example.

    Written by Scott Donaldson, V0.1, 25/06/2020

    References
    ----------
    [1] https://docs.scipy.org/doc/scipy/reference/constants.html for full units, but scipy takes
    them from CODATA Recommended Values of the Fundamental Physical Constants 2018.
    """

    # Make input lowercase such that si_in can be case insensitive and remove any trailing whitespace
    si_in_l = si_in.strip()
    si_in_l = si_in_l.lower()

    # Make sure input unit type is known
    if not check_unit(si_in_l):
        print("ERROR: Given si unit " + si_in_l + " not currently implemented")
        sys.exit(1)

    # General dimensionless atomic units
    if si_in_l=="atom"   : return si_in_val
    if si_in_l=="atomic" : return si_in_val

    # Length
    if si_in_l=="bohr" : return si_in_val
    if si_in_l=="m"    : return si_in_val * (c.m_e * c.c * c.alpha)/c.hbar
    if si_in_l=="cm"   : return si_to_atomic("m",si_in_val) * 1E-2
    if si_in_l=="nm"   : return si_to_atomic("m",si_in_val) * 1E-9
    if si_in_l=="a"    : return si_to_atomic("m",si_in_val) * 1E-10
    if si_in_l=="ang"  : return si_to_atomic("m",si_in_val) * 1E-10
    if si_in_l=="pm"   : return si_to_atomic("m",si_in_val) * 1E-12

    # Mass
    if si_in_l=="me"   : return si_in_val
    if si_in_l=="m_e"  : return si_in_val
    if si_in_l=="amu"  : return si_in_val * 1E-3/(c.N_A*c.m_e)
    if si_in_l=="kg"   : return si_in_val * 1/c.m_e
    if si_in_l=="g"    : return si_to_atomic("kg",si_in_val) * 1E-3

    # Time
    if si_in_l=="aut"  : return si_in_val
    if si_in_l=="s"    : return si_in_val * (c.c**2 * c.alpha**2 * c.m_e)/c.hbar
    if si_in_l=="ms"   : return si_to_atomic("s",si_in_val) * 1E-3
    if si_in_l=="mus"  : return si_to_atomic("s",si_in_val) * 1E-6
    if si_in_l=="ns"   : return si_to_atomic("s",si_in_val) * 1E-9
    if si_in_l=="ps"   : return si_to_atomic("s",si_in_val) * 1E-12
    if si_in_l=="fs"   : return si_to_atomic("s",si_in_val) * 1E-15

    # Charges
    if si_in_l=="e"        : return si_in_val
    if si_in_l=="c"        : return si_in_val * 1/c.e
    if si_in_l=="coulomb"  : return si_to_atomic("c",si_in_val)

    # Electric dipole moments
    if si_in_l=="d"        : return si_in_val * (1E-21/c.c) * si_to_atomic("c",1) * si_to_atomic("m",1)
    if si_in_l=="debye"    : return si_to_atomic("d",si_in_val)

    # Magnetic dipole moments
    if si_in_l=="mub"      : return si_in_val * (c.e * c.hbar)/(2 * c.m_e)
    if si_in_l=="magneton" : return si_to_atomic("mub",si_in_val)

    # Energies
    if si_in_l=="ha"        : return si_in_val
    if si_in_l=="hartree"   : return si_in_val
    if si_in_l=="mha"       : return si_in_val * 1E-3
    if si_in_l=="ev"        : return si_in_val * c.e/( c.alpha**2 * c.m_e * c.c**2 )
    if si_in_l=="mev"       : return si_to_atomic("ev",si_in_val) * 1E-3
    if si_in_l=="ry"        : return si_in_val * 0.5
    if si_in_l=="mry"       : return si_to_atomic("ry",si_in_val) * 1E-3
    if si_in_l=="j"         : return si_in_val * 1/( c.alpha**2 * c.m_e *c.c**2 )
    if si_in_l=="kj"        : return si_to_atomic("j",si_in_val) * 1E3
    if si_in_l=="erg"       : return si_in_val * si_to_atomic("j",1) * 1E-7
    if si_in_l=="kj.mol-1"  : return si_in_val * si_to_atomic("j",1)/( c.N_A ) * 1E3
    if si_in_l=="kj/mol"    : return si_to_atomic("kj.mol-1",si_in_val)
    if si_in_l=="kcal/mol"  : return si_in_val * si_to_atomic("kj/mol",1) * 4.184
    if si_in_l=="kcal.mo-1" : return si_to_atomic("kcal/mol",si_in_val)
    if si_in_l=="hz"        : return si_in_val * si_to_atomic("j",1) * c.hbar
    if si_in_l=="mhz"       : return si_to_atomic("hz",si_in_val) * 1E6
    if si_in_l=="thz"       : return si_to_atomic("hz",si_in_val) * 1E9
    if si_in_l=="ghz"       : return si_to_atomic("hz",si_in_val) * 1E12
    if si_in_l=="cm-1"      : return si_in_val * si_to_atomic("hz",1) * c.c * 1E2
    if si_in_l=="k"         : return si_in_val * c.k * si_to_atomic("j",1)

    # Entropy
    if si_in_l=="j/mol/k"   : return si_in_val / c.R
    if si_in_l=="jmol-1k-1" : return si_to_atomic("j/mol/k",si_in_val)

    # Forces
    if si_in_l=="ha/bohr"   : return si_in_val
    if si_in_l=="ha.bohr-1" : return si_to_atomic("ha/bohr",si_in_val)
    if si_in_l=="ev/a"      : return si_in_val * ( si_to_atomic("ev",1) / si_to_atomic("a",1) )
    if si_in_l=="ev.a-1"    : return si_to_atomic("ev/a",si_in_val)
    if si_in_l=="n"         : return si_in_val * ( si_to_atomic("j",1) / si_to_atomic("m",1) )
    if si_in_l=="dyne"      : return si_to_atomic("n",si_in_val) * 1E-5

    # Velocities
    if si_in_l=="auv"       : return si_in_val
    if si_in_l=="a/ps"      : return si_in_val * ( si_to_atomic("a",1) / si_to_atomic("ps",1) )
    if si_in_l=="a.ps-1"    : return si_to_atomic("a/ps",si_in_val)
    if si_in_l=="ang/ps"    : return si_to_atomic("a/ps",si_in_val)
    if si_in_l=="a/fs"      : return si_in_val * ( si_to_atomic("a",1) / si_to_atomic("fs",1) )
    if si_in_l=="a.fs-1"    : return si_to_atomic("a/fs",si_in_val)
    if si_in_l=="ang/fs"    : return si_to_atomic("a/fs",si_in_val)
    if si_in_l=="bohr/ps"   : return si_in_val * ( si_to_atomic("bohr",1) / si_to_atomic("ps",1) )
    if si_in_l=="bohr.ps-1" : return si_to_atomic("bohr/ps",si_in_val)
    if si_in_l=="bohr/ps"   : return si_to_atomic("bohr/ps",si_in_val)
    if si_in_l=="bohr/fs"   : return si_in_val * ( si_to_atomic("bohr",1) / si_to_atomic("fs",1) )
    if si_in_l=="bohr.fs-1" : return si_to_atomic("bohr/fs",si_in_val)
    if si_in_l=="bohr/fs"   : return si_to_atomic("bohr/fs",si_in_val)
    if si_in_l=="m/s"       : return si_in_val * ( si_to_atomic("m",1) / si_to_atomic("s",1) )
    if si_in_l=="m.s-1"     : return si_to_atomic("bohr/fs",si_in_val)

    # Pressures
    if si_in_l=="ha/bohr**3"      : return si_in_val
    if si_in_l=="ha.bohr-3"       : return si_in_val
    if si_in_l=="hartree/bohr**3" : return si_in_val
    if si_in_l=="ev/a**3"         : return si_in_val * (si_to_atomic("ev",1)/(si_to_atomic("a",1)**3 ))
    if si_in_l=="ev/a**3"         : return si_to_atomic("ev/a**3",si_in_val)
    if si_in_l=="ev/a**3"         : return si_to_atomic("ev/a**3",si_in_val)
    if si_in_l=="pa"              : return si_in_val * (si_to_atomic("n",1)/(si_to_atomic("m",1)**2 ))
    if si_in_l=="mpa"             : return si_to_atomic("pa",si_in_val) * 1E6
    if si_in_l=="gpa"             : return si_to_atomic("pa",si_in_val) * 1E9
    if si_in_l=="tpa"             : return si_to_atomic("pa",si_in_val) * 1E12
    if si_in_l=="ppa"             : return si_to_atomic("pa",si_in_val) * 1E15
    if si_in_l=="atm"             : return si_to_atomic("pa",si_in_val) * 101325.027
    if si_in_l=="bar"             : return si_to_atomic("pa",si_in_val) * 1E5

    # Reciprocal lengths
    if si_in_l=="1/bohr"      : return si_in_val
    if si_in_l=="bohr-1"      : return si_in_val
    if si_in_l=="1/m"         : return si_in_val / si_to_atomic("m",1)
    if si_in_l=="m-1"         : return si_to_atomic("1/m",si_in_val)
    if si_in_l=="1/nm"        : return si_in_val / si_to_atomic("nm",1)
    if si_in_l=="nm-1"        : return si_to_atomic("1/nm",si_in_val)
    if si_in_l=="1/pm"        : return si_in_val / si_to_atomic("pm",1)
    if si_in_l=="pm-1"        : return si_to_atomic("1/pm",si_in_val)
    if si_in_l=="1/a"         : return si_in_val / si_to_atomic("a",1)
    if si_in_l=="a-1"         : return si_to_atomic("1/a",si_in_val)

    # Force Constants
    if si_in_l=="ha/bohr**2"  : return si_in_val
    if si_in_l=="ha/bohr**2"  : return si_in_val
    if si_in_l=="ev/a**2"     : return si_in_val * (si_to_atomic("ev",1)/(si_to_atomic("a",1)**2 ))
    if si_in_l=="ev.a-2"      : return si_to_atomic("ev/a**2",si_in_val)
    if si_in_l=="n/m"         : return si_in_val * (si_to_atomic("n",1)/(si_to_atomic("m",1) ))
    if si_in_l=="n.m-1"       : return si_to_atomic("n/m",si_in_val)
    if si_in_l=="dyne/cm"     : return si_in_val * (si_to_atomic("dyne",1)/(si_to_atomic("cm",1) ))
    if si_in_l=="dyne.cm-1"   : return si_to_atomic("dyne/cm",si_in_val)

    # Volumes
    if si_in_l=="bohr**3" : return si_in_val
    if si_in_l=="m**3"    : return si_in_val * si_to_atomic("m",1)**3
    if si_in_l=="cm**3"   : return si_in_val * ( si_to_atomic("m",1) * 1E-2  )**3
    if si_in_l=="nm**3"   : return si_in_val * ( si_to_atomic("m",1) * 1E-9  )**3
    if si_in_l=="a**3"    : return si_in_val * ( si_to_atomic("m",1) * 1E-10 )**3
    if si_in_l=="pm**3"   : return si_in_val * ( si_to_atomic("m",1) * 1E-12 )**3

    # Magres
    if si_in_l=="acu"          : return si_in_val
    if si_in_l=="ampere"       : return si_in_val * (c.hbar/(c.e * c.hartree))
    if si_in_l=="acd"          : return si_in_val
    if si_in_l=="amperemetre2" : return si_in_val * (si_to_atomic("ampere",1) * (si_to_atomic("m",1)**2))
    if si_in_l=="ampere.m2"    : return si_to_atomic("amperemetre2",si_in_val)
    if si_in_l=="amfd"         : return si_in_val
    if si_in_l=="tesla"        : return si_in_val * (c.e * c.bohr_r**2)/c.hbar
    if si_in_l=="gauss"        : return si_to_atomic("tesla",si_in_val) * 1E-4
    if si_in_l=="agr"          : return si_in_val
    if si_in_l=="bohr2"        : return si_in_val
    if si_in_l=="bohr**2"      : return si_in_val
    if si_in_l=="fm2"          : return si_in_val * si_to_atomic("m",1)**2 * 1E-30
    if si_in_l=="barn"         : return si_in_val * si_to_atomic("m",1)**2 * 1E-28

    # Efield
    if si_in_l=="ha/bohr/e"     : return si_in_val
    if si_in_l=="ha.bohr-1.e-1" : return si_in_val
    if si_in_l=="ev/a/e"        : return si_in_val * ( si_to_atomic("ev",1)/si_to_atomic("a",1) )
    if si_in_l=="ev/ang/e"      : return si_to_atomic("ev/a/e",si_in_val)
    if si_in_l=="n/coulomb"     : return si_in_val * ((si_to_atomic("j",1)*c.e)/si_to_atomic("m",1))
    if si_in_l=="n.coulomb-1"   : return si_to_atomic("n/coulomb",si_in_val)


def atomic_to_si(si_out,atomic_in_val):
    """ Convert from dimensionless atomic units to Si units

    Convert the input float value atomic_in_value from dimensionless atomic units to the
    Si units given as a string in si_out.

    Conversion is carried out using the reciprocal unit conversion factor found by calling
    si_to_atomic.

    Parameters
    ----------
    si_out : string
        String input value giving the desired units to convert the `atomic_in_val` into
        from dimensionless atomic units.
        Unit names must be as defined in CASTEP module io.f90 (i.e. units CASTEP uses).
        `si_in` is case insensitive.
    atomic_in_val : float
        Value to be converted from dimensionless atomic units to the units given as string in si_out.

    Returns
    -------
    float
        The value atomic_in_val converted from dimensionless atomic units to those given in si_out.

    Notes
    -----
    Constants values used (in `si_to_atomic`) are those within the scipy.constants module [1], imported
    as c. This allows for calls like c.m_e for electron mass for example.

    Written by Scott Donaldson, V0.1, 25/06/2020

    References
    ----------
    [1] https://docs.scipy.org/doc/scipy/reference/constants.html for full units, but scipy takes
    them from CODATA Recommended Values of the Fundamental Physical Constants 2018.
    """
    atomic_in_val = np.asarray(atomic_in_val, dtype=float)
    res = atomic_in_val * ( 1 / si_to_atomic(si_out,1) )
    if np.isscalar(atomic_in_val):
        return res.item()
    else:
        return res


def si_to_si(si_in,si_out,si_val):
    """
    Convert the value si_val from units given as si_in into units of si_out.

    This is done by converting si_val from si_in to atomic units then from
    atomic units back to si_out units.

    It is required that the input and output units have the same dimension or
    the returned value is meaningless.

    NOTE: A result will be returned even if the input and output dimensions do
    not match. If they do not match the result is nonsense.

    Parameters
    ----------
    si_in : string
        The unit symbol for the input units to be converted from.
    si_out : string
        The unit symbol for the output units to be converted into.
    si_val : float
        Value in units of `si_in` to be converted to units of `si_out`.

    Returns
    -------
    float
        The value si_val converted from `si_in` units to `si_out` units. This is done by converting
        `si_val` to atomic units then from atomic units to `si_out` units.
        NOTE: Units must be converted to other units with the same dimensions.
        NOTE: A float value will be returned even if the dimensions of the input
        and output do not match.

    Notes
    -----
    Constants used for the constant values are those within the scipy.constants module [1], imported
    as c. This allows for calls like c.m_e for electron mass for example.

    Written by Scott Donaldson, V0.1, 23/07/2020

    References
    ----------
    [1] https://docs.scipy.org/doc/scipy/reference/constants.html for full units, but scipy takes
    them from CODATA Recommended Values of the Fundamental Physical Constants 2018.
    """
    si_val = np.asarray(si_val, dtype=float)
    res = atomic_to_si( si_out, si_to_atomic(si_in,si_val) )
    if np.isscalar(si_val):
        return res.item()
    else:
        return res


if __name__ == '__main__':
    """ Convert units by calling from the command line

    Method to calcualte a conversion from dimensionless atomic units to some
    given units or vice versa.

    This allows for conversion to be carried out on the command line by calling
    this file with three command line arguments, the input units, the output
    units and the value to convert. A single float is then returned, the value
    converted into the requisite units.

    Note that dimensionless atomic units are given by either "atom" or "atomic"

    Parameters
    ----------
    arg 1 : string
        "Input Units" : The input units to be converted from. This must be an unbroken
        string using giving one of the vales recognised by `si_to_atomic`. If "atom" or
        "atomic" are given units are taken to be dimensionless atomic units.
        This input is case insensitive, but must be an unbroken string.
    arg 2 : string
        "Output Units" : The units to convert into from the input units. "atom" or
        "atomic" signify dimensionless atomic units. This input is case insensitive
        but must be an unbroken string.
    arg 3 : float
        "Input Value" : The alue to convert from the input unit into the output unit.

    Returns
    -------
    float
        A single float is returned. The input value (`arg 3`) converted from the input
        units (`arg 1`) to the output units (`arg 2`).

    Notes
    -----
    Written by Scott Donaldson, V0.1, 25/06/2020
    """

    # Check for correct number of inputs
    if len(sys.argv) != 4:
        print("Wrong number of inputs, need IN_UNITS, OUT_UNITS, VALUE")
        sys.exit(1)

    if str(sys.argv[1].lower()) == "atomic" or str(sys.argv[1].lower()) == "atom" :
        # Convert from atomic units to si units
        print(atomic_to_si(str(sys.argv[2]),float(sys.argv[3])))
    elif str(sys.argv[2].lower()) == "atomic" or str(sys.argv[2].lower()) == "atom" :
        # Convert from Si units to atomic units
        print(si_to_atomic(str(sys.argv[1]),float(sys.argv[3])))
    else:
        # Convert between si units
        print(si_to_si(str(sys.argv[1]).lower(),str(sys.argv[2]).lower(),float(sys.argv[3])))
