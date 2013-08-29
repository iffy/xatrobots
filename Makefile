.PHONY: test pyflakes clean

clean:
	-rm -rf _trial_temp
	find . -name '*.pyc' -exec rm {} \;

test:
	trial xatro
	pyflakes xatro

pyflakes:
	pyflakes xatro