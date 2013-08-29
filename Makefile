.PHONY: test pyflakes clean

test: clean
	trial xatro
	pyflakes xatro

pyflakes:
	pyflakes xatro

clean:
	-rm -rf _trial_temp
	find . -name '*.pyc' -exec rm {} \;