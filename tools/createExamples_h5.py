#!/usr/bin/env python
#
# Copyright (c) 2015, Axel Huebl, Remi Lehe
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import h5py as h5
import numpy as np
import sys
import datetime
from dateutil.tz import tzlocal

def setup_root_attr(f, iteration):
    """
    Write the root metadata for this file
    
    Parameter
    ---------
    f : an h5py.File object
        The file in which to write the data
    """

    # Required attributes
    f.attrs["version"] = "1.0.0"
    f.attrs["basePath"] = "/data/%d/" % iteration
    f.attrs["fieldsPath"] = "fields/"
    f.attrs["particlesPath"] = "particles/"
    f.attrs["iterationEncoding"] = "fileBased"
    f.attrs["iterationFormat"] = "/data/%T/"

    # Recommended attributes
    f.attrs["author"] = "Axel Huebl <a.huebl@hzdr.de>"
    f.attrs["software"] = "OpenPMD Example Script"
    #f.attrs["softwareVersion"] = "1.0.0"
    f.attrs["date"] = datetime.datetime.now(tzlocal()).strftime('%Y-%m-%d %H:%M:%S %z')

    # Optional
    f.attrs["comment"] = "This is a dummy file for test purposes."


def write_rho_cylindrical(f, mode0, mode1):
    """
    Write the metadata and the data associated with the scalar field rho, 
    using the cylindrical representation (with azimuthal decomposition going up to m=1)
    
    Parameters
    ----------
    f : an h5py.File object
        The file in which to write the data    
        
    mode0 : a 2darray of reals
        The values of rho in the azimuthal mode 0, on the r-z grid
        (The first axis corresponds to r, and the second axis corresponds to z)
        
    mode1 : a 2darray of complexs
        The values of rho in the azimuthal mode 1, on the r-z grid
        (The first axis corresponds to r, and the second axis corresponds to z)
    """
    # Path to the rho fields, within the h5py file
    full_rho_path = f.attrs["basePath"] + f.attrs["fieldsPath"] + "rho" 

    # Create the dataset (cylindrical representation with azimuthal modes up to m=1)
    # The first axis has size 2m+1 
    f.create_dataset( full_rho_path, (3, mode0.shape[0], mode0.shape[1]), dtype='f4')  
    f[full_rho_path].attrs["geometry"] = "cylindrical"    
    f[full_rho_path].attrs["geometryParameters"] = "m=1; imag=+"
    
    # Add information on the units of the data
    f[full_rho_path].attrs["unitSI"] = 1.0
    f[full_rho_path].attrs["unitDimension"] = \
       np.array([-3.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0 ])
       #           L    M    T    J  theta  N    J
       # rho is in Coulomb per meter cube : C / m^3 = A * s / m^3 -> M^-3 * T * J

    # Add time information
    f[full_rho_path].attrs["time"] = 0.  # Time is expressed in nanoseconds here
    f[full_rho_path].attrs["timeUnitSI"] = 1.e-9  # Conversion from nanoseconds to seconds

    # Add information on the r-z grid
    f[full_rho_path].attrs["gridSpacing"] = np.array([1.0, 1.0])  # dr, dz
    f[full_rho_path].attrs["gridGlobalOffset"] = np.array([0.0, 0.0]) # rmin, zmin
    f[full_rho_path].attrs["position"] = np.array([0.0, 0.0])    
    f[full_rho_path].attrs["gridUnitSI"] = 1.0
    f[full_rho_path].attrs["dataOrder"] = "C"

    # Add specific information for PIC simulations
    add_EDPIC_attr_fields(f, full_rho_path)
    
    # Fill the array with the field data 
    if mode0.shape != mode1.shape :
        raise ValueError("`mode0` and `mode1` should have the same shape")
    f[full_rho_path][0,:,:] = mode0[:,:] # Store the mode 0 first
    f[full_rho_path][1,:,:] = mode1[:,:].real # Then store the real part of mode 1
    f[full_rho_path][2,:,:] = mode1[:,:].imag # Then store the imaginary part of mode 1


def write_e_2d_cartesian(f, data_ex, data_ey, data_ez ):
    """
    Write the metadata and the data associated with the vector field E, 
    using a 2d Cartesian representation
    
    Parameters
    ----------
    f : an h5py.File object
        The file in which to write the data    
        
    data_ex, data_ey, data_ez : 2darray of reals
        The values of the components ex, ey, ez on the 2d x-y grid
        (The first axis corresponds to x, and the second axis corresponds to y)
    """
    # Path to the E field, within the h5py file
    full_e_path = f.attrs["basePath"] + f.attrs["fieldsPath"] + "E/" 

    # Create the dataset (2d cartesian grid)
    f.create_dataset(full_e_path + "x", data_ex.shape, dtype='f4')
    f.create_dataset(full_e_path + "y", data_ey.shape, dtype='f4')
    f.create_dataset(full_e_path + "z", data_ez.shape, dtype='f4')

    # Write the common metadata for the group
    f[full_e_path].attrs["geometry"] = "cartesian"
    f[full_e_path].attrs["gridSpacing"] = np.array([1.0, 1.0])       # dx, dy
    f[full_e_path].attrs["gridGlobalOffset"] = np.array([0.0, 0.0])  # xmin, ymin    
    f[full_e_path].attrs["gridUnitSI"] = 1.0
    f[full_e_path].attrs["dataOrder"] = "C"
    f[full_e_path].attrs["unitDimension"] = \
       np.array([1.0, 1.0, -3.0, -1.0, 0.0, 0.0, 0.0 ])
       #          L    M     T     J  theta  N    J
       # E is in volts per meters : V / m = kg * m / (A * s^3) -> L * M * T^-3 * J^-1

    # Add specific information for PIC simulations at the group level
    add_EDPIC_attr_fields(f, full_e_path)

    # Add time information
    f[full_e_path].attrs["time"] = 0.  # Time is expressed in nanoseconds here
    f[full_e_path].attrs["timeUnitSI"] = 1.e-9  # Conversion from nanoseconds to seconds
    
    # Write attribute that is specific to each dataset: staggered position within a cell
    f[full_e_path + "x"].attrs["position"] = np.array([0.0, 0.5])
    f[full_e_path + "y"].attrs["position"] = np.array([0.5, 0.0])
    f[full_e_path + "z"].attrs["position"] = np.array([0.0, 0.0])
    
    # Fill the array with the field data 
    f[full_e_path + "x"][:,:] =  data_ex[:,:]
    f[full_e_path + "y"][:,:] =  data_ey[:,:]
    f[full_e_path + "z"][:,:] =  data_ez[:,:]


def add_EDPIC_attr_fields(f, fieldName ):
    """
    Write the metadata which is specific to PIC algorithm
    for a given field
    
    Parameters
    ----------
    f : an h5py.File object
        The file in which to write the data
        
    fieldName : string
        The path (within the HDF5 file) to the field considered
        (a path to a dataset in the case of a scalar field, 
        or to a group in the case of a vector field)
    """
    f[fieldName].attrs["fieldSolver"] = "Yee"
    f[fieldName].attrs["fieldSolverOrder"] = 2.0
    #f[fieldName].attrs["fieldSolverParameters"] = ""
    f[fieldName].attrs["fieldSmoothing"] = "none"
    #f[fieldName].attrs["fieldSmoothingParameters"] = \
    # "period=10;numPasses=4;compensator=true"
    f[fieldName].attrs["currentSmoothing"] = "none"
    #f[fieldName].attrs["currentSmoothingParameters"] = \
    #"period=1;numPasses=2;compensator=false"
    f[fieldName].attrs["chargeCorrection"] = "none"
    #f[fieldName].attrs["chargeCorrectionParameters"] = "period=100"

def add_EDPIC_attr_particles(f, particleName):
    """
    Write the metadata which is specific to the PIC algorithm
    for a given species.

    Parameters
    ----------
    f : an h5py.File object
        The file in which to write the data

    particleName : string
        The path (within the HDF5 file) to the species considered
        (a path to a dataset in the case of a scalar field, 
        or to a group in the case of a vector field)
    """
    f[particleName].attrs["particleShape"] = 3.0
    f[particleName].attrs["currentDeposition"] = "Esirkepov"
    #f[particleName].attrs["currentDepositionParameters"] = ""
    f[particleName].attrs["particlePush"] = "Boris"
    f[particleName].attrs["particleInterpolation"] = "Trilinear"
    f[particleName].attrs["particleSmoothing"] = "none"
    #f[particleName].attrs["particleSmoothingParameters"] = "period=1;numPasses=2;compensator=false"

def write_particles(f):
    fullParticlesPath = f.attrs["basePath"] + f.attrs["particlesPath"]

    # constant scalar particle attributes (that could also be variable data sets)
    f.create_group(fullParticlesPath + "electrons/charge")
    f[fullParticlesPath + "electrons/charge"].attrs["value"] = -1.0;
    f[fullParticlesPath + "electrons/charge"].attrs["unitSI"] = 1.60217657e-19;
    f[fullParticlesPath + "electrons/charge"].attrs["unitDimension"] = \
       np.array([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0 ])
       #          L    M    T    J  theta  N    J
       # C = A * s
    f.create_group(fullParticlesPath + "electrons/mass")
    f[fullParticlesPath + "electrons/mass"].attrs["value"] = 1.0;
    f[fullParticlesPath + "electrons/mass"].attrs["unitSI"] = 9.10938291e-31;
    f[fullParticlesPath + "electrons/mass"].attrs["unitDimension"] = \
       np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0 ])
       #          L    M    T    J  theta  N    J

    f[fullParticlesPath + "electrons"].attrs["longName"] = "My first electron species"
    addEDPICAttrParticles(f, fullParticlesPath + "electrons")

    # scalar particle attribute (non-const/individual per particle)
    f.create_dataset(fullParticlesPath + "electrons/weighting", (128,), dtype='f4')
    f[fullParticlesPath + "electrons/weighting"].attrs["unitSI"] = 1.0;
    f[fullParticlesPath + "electrons/weighting"].attrs["unitDimension"] = \
       np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ]) # plain floating point number

    # vector particle attribute (non-const/individual per particle)
    f.create_dataset(fullParticlesPath + "electrons/position/x", (128,), dtype='f4')
    f.create_dataset(fullParticlesPath + "electrons/position/y", (128,), dtype='f4')
    f.create_dataset(fullParticlesPath + "electrons/position/z", (128,), dtype='f4')
    f[fullParticlesPath + "electrons/position"].attrs["unitSI"] = 1.e-9;
    f[fullParticlesPath + "electrons/position"].attrs["unitDimension"] = \
       np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ])
       #          L    M     T    J  theta  N    J
       # Dimension of Length per component

    f.create_dataset(fullParticlesPath + "electrons/momentum/x", (128,), dtype='f4')
    f.create_dataset(fullParticlesPath + "electrons/momentum/y", (128,), dtype='f4')
    f.create_dataset(fullParticlesPath + "electrons/momentum/z", (128,), dtype='f4')
    f[fullParticlesPath + "electrons/momentum"].attrs["unitSI"] = 1.60217657e-19;
    f[fullParticlesPath + "electrons/momentum"].attrs["unitDimension"] = \
       np.array([1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0 ])
       #          L    M     T    J  theta  N    J
       # Dimension of Length * Mass / Time



if __name__ == "__main__":
	
	# Open an exemple file
    f = h5.File("example.h5", "w")
    
    # Setup the root attributes for iteration 0
    setup_root_attr(f, iteration=0 )
    
    # Write the field data to this file. 
    # (Here the data is randomly generated, but in an actual simulation, this would 
    # be replaced by the simulation data.)
    # - Write rho
    # Mode 0 : real values, mode 1 : complex values
    data_rho0 = np.random.rand(32,64)
    data_rho1 = np.random.rand(32,64) + 1.j*np.random.rand(32,64) 
    write_rho_cylindrical(f, data_rho0, data_rho1)
    # - Write E
    data_ex = np.random.rand(32,64)
    data_ey = np.random.rand(32,64)
    data_ez = np.random.rand(32,64)
    write_e_2d_cartesian( f, data_ex, data_ey, data_ez )
    
    # writeParticles(f)
    
    # Close the file
    f.close()
    print("File example.h5 created!")