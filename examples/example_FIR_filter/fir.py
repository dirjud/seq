import seq, math
from seq import Bin, Sequence

N = 16 # number of taps in the FIR filter

B = 8  # bit depth of input stream
C = 8  # bit depth of FIR filter tap coefficients
A = 20 # bit depth of accumulator in the FIR filter

widthN = math.ceil(math.log(N+1,2))

# create the signal definitions
xin   = seq.Signal(name="xin",  width=B,   signed=True)
coeff = seq.Signal(name="coeff",width=C,   signed=True)
mult  = seq.Signal(name="mult", width=B+C, signed=True)
xout  = seq.Signal(name="xout", width=A,   signed=True)
addr  = seq.Signal(name="addr", width=widthN)

# Create the base fir Bin. This Bin will have the basic
# sequences necessary to create a MAC (Multiply, ACcumulate)
# and to reset it.
fir_base = Bin.Bin(
    name = "fir_base",
    regs = [mult, xout],
    seqs = [
        # Create a reset Sequence that can reset the output accumulator
        # between samples.
        Sequence.Set(name="reset", set=dict(xout=0)),

        # Implement a multiplier that can multiply tap coefficients
        # and the input stream. This is a serial multiplier, which
        # means it is slower but smaller than a single clock multiply.
        # If speed is essential, change this to a Sequence.Multiply
        # instead.
        Sequence.SerialMultiply(name="mult", a=xin, b=coeff, out=mult),

        # Create an accumulating sequence by adding the output of the
        # multipler with the output register.
        Sequence.Add(name="accum", a=mult, b=xout, out=xout, clamp=True),
        ]
    )
    
# This Bin implements the higher level sequences of an FIR filter.
# The Repeat sequence is used to cycle through 
fir = Bin.Bin(
    name = "fir",
    children = [fir_base],
    seqs = [
        # The complete filter is implemented as Serial sequence that
        # has some embeded Sequences to Repeat the multipy/accumulate
        # N times. The Repeat sequences outputs its internal counter
        # as the signal 'addr' so that we can hook that up to the
        # buffers holding the input stream and FIR filter
        # coefficients.
        Sequence.Serial(
            ["reset", 
             Sequence.Repeat(count=N,
                             counter=addr,
                             subseq=Sequence.Serial(["mult", "accum"])),
             ],
            ),
        ],
    )

fir.vlog_dump(recurse=True)
