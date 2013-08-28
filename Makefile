.PHONY: test pyflakes

test:
	trial xatro
	pyflakes xatro

pyflakes:
	pyflakes xatro