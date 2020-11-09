library("ggplot2")

data <- read.table("osm-mon-collectors.data", col.names = c("Uptime","Count"))

cairo_pdf("osm-mon-collectors.pdf", width=15, height=10, family="Helvetica", pointsize=22)

p <- ggplot(data,
            aes(x = Uptime,
                y = Count)
           ) +
        geom_line(color="red", size=2) +
        theme(title             = element_text(size=32),
              plot.title        = element_text(size=20, hjust = 0.5, face="bold"),
              axis.title        = element_text(size=20, face="bold"),
              strip.text        = element_text(size=18, face="bold"),
              axis.text.x       = element_text(size=16, angle=90, face="bold", colour="black"),
              axis.text.y       = element_text(size=16, angle=90, hjust=0.5, colour="black"),
              legend.title      = element_blank(),
              legend.text       = element_text(size=18, face="bold"),
              legend.background = element_rect(colour = "blue",  fill = "#ffffaa55", size=1),
             ) +
        labs(title = "Number of osm-mon-collector Processes",
             x     = "Uptime [s]",
             y     = "Number of osm-mon-collector Processes")
print(p)

dev.off()
