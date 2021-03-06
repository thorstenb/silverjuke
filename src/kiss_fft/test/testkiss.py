#!/usr/bin/env python2.3

import math
import sys
import os
import random
import struct
import popen2
import getopt
import Numeric
import FFT

pi=math.pi
e=math.e
j=complex(0,1)

doreal=0

datatype = os.environ.get('DATATYPE','float')

util = '../tools/fft'
fmt='f'
minsnr=90
if datatype == 'double':
    util = '../tools/fft_double'
    fmt='d'
elif datatype=='short':
    util = '../tools/fft_short'
    fmt='h'
    minsnr=10


def dopack(x,cpx=1):
    x = Numeric.reshape( x, ( Numeric.size(x),) )
    if cpx:
        s = ''.join( [ struct.pack(fmt*2,c.real,c.imag) for c in x ] )
    else:
        s = ''.join( [ struct.pack(fmt,c) for c in x ] )
    return s

def dounpack(x,cpx):
    uf = fmt * ( len(x) / struct.calcsize(fmt) )
    s = struct.unpack(uf,x)
    if cpx:
        return Numeric.array(s[::2]) + Numeric.array( s[1::2] )*j
    else:
        return Numeric.array(s )

def make_random(dims=[1]):
    res = []
    for i in range(dims[0]):
        if len(dims)==1:
            r=random.uniform(-1,1)
            if doreal:
                res.append( r )
            else:
                i=random.uniform(-1,1)
                res.append( complex(r,i) )
        else:
            res.append( make_random( dims[1:] ) )
    return Numeric.array(res)

def flatten(x):
    ntotal = Numeric.product(Numeric.shape(x))
    return Numeric.reshape(x,(ntotal,))

def randmat( ndims ):
    dims=[]
    for i in range( ndims ):
        curdim = int( random.uniform(2,4) )
        dims.append( curdim )
    return make_random(dims )

def test_fft(ndims):
    if ndims == 1:
        nfft = int(random.uniform(50,520))
        if doreal:
            nfft = int(nfft/2)*2

        x = Numeric.array(make_random( [ nfft ] ) )
    else:
        x=randmat( ndims )

    print 'dimensions=%s' % str( Numeric.shape(x) ),
    if doreal:
        xver = FFT.real_fftnd(x)
    else:
        xver = FFT.fftnd(x)
    
    x2=dofft(x)
    err = xver - x2
    errf = flatten(err)
    xverf = flatten(xver)
    errpow = Numeric.vdot(errf,errf)+1e-10
    sigpow = Numeric.vdot(xverf,xverf)+1e-10
    snr = 10*math.log10(abs(sigpow/errpow) )
    print 'SNR (compared to NumPy) : %.1fdB' % float(snr)

    if snr<minsnr:
        print 'xver=',xver
        print 'x2=',x2
        print 'err',err
        sys.exit(1)
 
def dofft(x):
    dims=list( Numeric.shape(x) )
    x = flatten(x)
    iscomp = (type(x[0]) == complex)

    scale=1
    if datatype=='short':
        x = 32767 * x
        scale = len(x) / 32767.0

    cmd='%s -n ' % util
    cmd += ','.join([str(d) for d in dims])
    if doreal:
        cmd += ' -R '

    p = popen2.Popen3(cmd )

    p.tochild.write( dopack( x , iscomp ) )
    p.tochild.close()

    res = dounpack( p.fromchild.read() , 1 )
    if doreal:
        dims[-1] = int( dims[-1]/2 ) + 1

    res = scale * res

    p.wait()
    return Numeric.reshape(res,dims)

def main():
    opts,args = getopt.getopt(sys.argv[1:],'r')
    opts=dict(opts)

    global doreal
    doreal = opts.has_key('-r')

    if doreal:
        print 'Note: Real optimization not yet done for odd length ffts and multi-D'
        test_fft(1)
    else:
        for dim in range(1,9):
            test_fft( dim )
        print 'We crossed the 8th dimension.  Buckaroo would be proud'

if __name__ == "__main__":
    main()

