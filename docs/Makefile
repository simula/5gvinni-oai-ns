mdfiles   := $(wildcard *.md)
htmlfiles := $(patsubst %.md,%.html,$(mdfiles))

.PHONY:	all
all:	$(htmlfiles)

$(htmlfiles):	%.html:	%.md
	pandoc $< >$@
