import seq
from seq import Bin, Sequence

# create the signal definitions
xin   = seq.Signal(name="xin",  width=8,   signed=True)
coeff = seq.Signal(name="coeff",width=8,   signed=True)
mult  = seq.Signal(name="mult", width=16,  signed=True)
xout  = seq.Signal(name="xout", width=20,  signed=True)

# Create the base fir Bin that has the basic sequences necessary to
# create a MAC (Multiply, ACcumulate) and to reset it.
fir_base = Bin.Bin(
    name = "fir_base",
    regs = [mult, xout],
    seqs = [
        # Create a sequence to reset the output accumulator
        Sequence.Set(name="reset", set=dict(xout=0)),

        # Implement a multiplier that can multiply tap coeffs and
        # input samples. This is a serial multiplier, which means it
        # is slower but smaller than a single clock multiply.  If
        # speed is essential, change this to a Sequence.Multiply.
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
        # The complete filter is implemented as a Serial sequence that
        # has some embeded sequences to Repeat the multipy/accumulate
        # 16 times.
        Sequence.Serial(
            ["reset", 
             Sequence.Repeat(count=16,  # number of taps in the FIR filter
                             counter=seq.Signal(name="addr", width=5),
                             subseq=Sequence.Serial(["mult", "accum"])),
             ],
            ),
        ],
    )
fir.vlog_dump(recurse=True)
