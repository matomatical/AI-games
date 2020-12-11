LATEX      := latexmk
LATEXFLAGS := -pdf

# source files
TEXS := $(wildcard *.tex)
PDFS := $(patsubst %.tex, %.pdf, $(TEXS))

# default target: make all pdfs
all: $(PDFS) clean

# independent pdfs depend on source only
%.pdf: %.tex makefile $(DOCS)
	$(LATEX) $(LATEXFLAGS) $<
	texcount -sum -1 $<
clean:
	latexmk -c
clobber:
	latexmk -C
todos:
	-grep "TODO" $(TEXS)

.PHONY: all clean clobber todos
