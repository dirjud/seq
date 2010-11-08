all:
	python test.py
	iverilog -o test.vvp test_tb.v test1.v
	vvp test.vvp

clean:
	rm -f ~* *.vcd *.vvp test1.v
