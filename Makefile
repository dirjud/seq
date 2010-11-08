all:
	make -C ../seq/doc html
	cp ../seq/doc/build/html/*html .
	cp ../seq/doc/build/html/_images/*png _images/
	cp ../seq/doc/build/html/_static/*css _static/
	cp ../seq/doc/build/html/_sources/*txt _sources/
