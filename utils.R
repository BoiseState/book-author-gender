library(tidyverse)

source_notebook = function(path) {
    nb = rjson::fromJSON(file=path)
    message("loading notebook with ", length(nb$cells), " cells")
    code = map_dfr(nb$cells, function(c) { 
            data_frame(type=c$cell_type, lines=c$source) 
        }) %>%
        filter(type == "code") %>%
        pull(lines) %>%
        paste(collapse="\n")
    cxn = textConnection(code)
    source(cxn)
    close(cxn)
}

drawplot = function(plot, file=NA, width=5, height=3, ...) {
    if (!is.na(file)) {
        png(paste(file, "png", sep="."), width=width, height=height, units='in', res=600, ...)
        print(plot)
        dev.off()
        cairo_pdf(paste(file, "pdf", sep="."), width=width, height=height, ...)
        print(plot)
        dev.off()
    }
    plot
}

density_frame = function(xs, ...) {
    dens = density(xs, ...)
    data_frame(value=dens$x, density=dens$y)
}

theme_paper = function() {
    # theme_minimal(base_size=10, base_family='Source Sans Pro') +
    theme_minimal(base_size=10) +
         theme(panel.border=element_rect(linetype="solid", color="grey", fill=NA),
               plot.margin=margin())
}
