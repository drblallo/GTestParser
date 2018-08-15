
python import sys
pyfile expand('<sfile>:p:h')/python/GTestParser.py

function! RunOnBuffer()
    py runOnBuffer()
endfunction

command RunOnBuffer call RunOnBuffer()

function! ApplyTestSyntax()

	syntax keyword failed KO
	syntax keyword success OK

	hi failed ctermfg=1
	hi success ctermfg=34
endfunction
