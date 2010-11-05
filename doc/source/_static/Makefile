all: sequence.pdf serial_sequence.pdf sequence_timing.pdf bin.pdf bin_exploded.pdf bin_timing.pdf


%.pdf: %.fig
	fig2dev -Lpdf $< $@
	fig2dev -Lpng -m2.0 $< $*.png