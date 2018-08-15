
python import sys
exec "pyfile " . expand('<sfile>:p:h') . "/python/GTestParser.py"

function! RunOnBuffer()
    py runOnBuffer()
endfunction

command! RunOnBuffer call RunOnBuffer()

function! ApplyTestSyntax()

	syntax keyword failed KO
	syntax keyword success OK

	hi failed ctermfg=1
	hi success ctermfg=34
endfunction

function! GetNearestTestLine()

	let s:currentLine = line(".")
	while s:currentLine >= 0
		let s:line = getline(s:currentLine)
		if match(s:line, 'TEST\(_F\)\=\s*(\s*.*\s*,\s*.*\s*).*') != -1
			return s:line
		endif
		let s:currentLine = s:currentLine - 1
			
	endwhile
	return ""

endfunction

function! GetSplittedNearest()
	
	let s:line = GetNearestTestLine()
	if s:line == ""
		return ""
	endif

	let s:line = split(s:line, "(")[1]	
	let s:line = split(s:line, ")")[0]

	let s:line = split(s:line, ",")

	return s:line
endfunction

function! GetNearestTestSuit()
	let s:both = GetSplittedNearest()

	let s:testSuite = s:both[0]
	
	return Strip(s:testSuite) 
endfunction

function! Strip(input_string)
    return substitute(a:input_string, '^\s*\(.\{-}\)\s*$', '\1', '')
endfunction

function! GetNearestTestCase()
	let s:both = GetSplittedNearest()

	let s:testSuite = s:both[1]
	
	return Strip(s:testSuite) 
endfunction

function! GTestOption(allSuit)
	if a:allSuit == 1
		return "--gtest_filter=".GetNearestTestSuit().".*"	
	else
		return "--gtest_filter=".GetNearestTestSuit().".".GetNearestTestCase()

	endif
endfunction
