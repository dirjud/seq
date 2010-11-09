FIR Filter Example
==================

Now we create a more interesting example and implement an FIR
filter. This will introduce two new concepts of registers and
hierarchy.

Here is the code to generate a simple FIR filter.

.. literalinclude:: ../../examples/example_FIR_filter/fir.py
   :linenos:

Here you can see an example of this FIR filter in action when 
simulated with tap coefficients that are uniform (implements
a moving average) and random input samples.

.. image:: ../../examples/example_FIR_filter/fir_example.png

Registers
---------

The member registers of a bin are specified using the ``regs`` keyword
as shown on Line 14. In this example, there are two registers that the
``fir_base`` bin controls.  These registers ``mult`` and ``xout``
registers get specified on lines 7 and 8 as signed 16 bit and 20 bit
signals, respectively and become outputs of the module. The ``mult``
register is gets set to the multiplication of ``xin`` and ``coeff``
(line 23) via the SerialMultiply sequence. The Add sequence on line
27 then add the ``mult`` register to the ``xout`` register. The
``xout`` register can also get set to 0 via the Set sequence
on line 17.


Hierarchy
---------

This example also introduces bin hierarchy. The ``fir`` bin uses the
``children`` keyword (line 35) to make the ``fir_base`` a member bin
of the ``fir`` bin. A given bin can only be the child of one bin.  The
parent can execute any of the child named child sequences. A sequence
is named by using the name keyword as shown on lines 17, 23, and 27
where the child sequences are name ``reset``, ``mult``, and ``accum``.
Names must be unique and adhere to verilog naming conventions.  The
parent uses sequences such as Sequence.Serial, Sequence.Parallel,
Sequence.Select, and Sequence.Child to execute the child
sequences. A Sequnce.Serial is used in this example (line 40) to execute
child sequences sequentially. The first sequence is "reset" (line 41). A
string can be used as shorthand for::

  Sequence.Child("reset")

In line 42 we see the second sequence to be executed is not a child
sequence but actually a Sequence.Repeat sequence. This sequence
repeats the provided "subseq" "count" number of times. "count" can
be a integer as in the case, or it can be a signal if it should be
specified as an input. The "subseq" in the example (line 44) is
a Serial sequence that executes child sequences "mult", and "accum".
This forms a MAC (Mulitply ACcumulate) regigster that is repeated 16
times. On line 43, the Repeat counter is exported as a signal called
"addr". This becomes an output of the module that we use to hook
up the buffers containing the input stream and tap coefficients
so that the correct data can be sent into the MAC. 


Top Level
---------

To use this FIR implementation requires writing some custom verilog
to hook up the buffers for the tap coefficients and the input samples
and to interface to those buffers based on the address being exported
by the generated code. Following the verilog that does this.

.. literalinclude:: ../../examples/example_FIR_filter/fir_top.v

For this implementation, the input stream must be much slower than the
clock rate to give time to serially multiply and accumulate the 16
taps for each sample.
