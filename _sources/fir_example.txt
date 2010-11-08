FIR Filter Example
==================

Now we create a more interesting example and implement an FIR
filter. This will introduce two new concepts of registers and ``Bin``
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

The member registers of a ``Bin`` are specified using the ``regs``
keyword as shown on Line 14. In the FIR example, there are two
registers that the ``fir_base`` Bin controls.  These registers are
exported as outputs of the module. The ``mult`` and ``xout`` registers
get specified on lines 7 and 8 as signed 16 bit and 20 bit signals,
respectively. The ``mult`` register is controlled by the
SerialMultiply Sequence specified as a member sequence on line 23.


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
