FROM qmcgaw/latexdevcontainer
#/usr/local/texlive/2021/texmf-dist/tex/latex/infwarerr/infwarerr.sty
# install libs used by this repo 
RUN apt -y install texlive-fonts-recommended
RUN tlmgr install setspace calc ifthen ifpdf ifxetex tocbibind appendix dvipsnames epstopdf graphicx datetime lineno everypage textpos biblatex natbib textcomp fourier lmodern inputenc fontenc microtype amsfonts amsmath amssymb hyperref geometry url breakurl fancyhdr nomencl makeidx
RUN tlmgr install fmtcount xkeyval nomencl setspace
RUN tlmgr install setspace tocbibind appendix infwarerr
