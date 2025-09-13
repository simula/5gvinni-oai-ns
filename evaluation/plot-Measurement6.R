#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# =====================================================================
#     #######  #####          #     #   ###   #     # #     #   ###
#     #       #     #         #     #    #    ##    # ##    #    #
#     #       #               #     #    #    # #   # # #   #    #
#      #####  #  ####  #####  #     #    #    #  #  # #  #  #    #
#           # #     #          #   #     #    #   # # #   # #    #
#     #     # #     #           # #      #    #    ## #    ##    #
#      #####   #####             #      ###   #     # #     #   ###
# =====================================================================
#
# SimulaMet OpenAirInterface Evolved Packet Core VNF and NS
# Copyright (C) 2019-2023 by Thomas Dreibholz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: dreibh@simula.no

library(ggplot2)
library(Hmisc)

source("/usr/share/netperfmeter/plotter.R")


name <- "Measurement6"



# Colours:
# colorsFiber <- c("orange","salmon")
# colorsADSL  <- c("green","forest green","royal blue","blue")
# plotColours <- topo.colors(2)
# c("royal blue", "blue",
#                  "orange","salmon", "red", "black", "gray")
plotColours <- c("royal blue", "orange", "gray")



makePlot <- function(node)
{
   if(node == "passive") {
      allResults <- loadResults(paste(sep="", name, "/passive.flow-ReceivedBitRate.data.bz2"))
      pSet   <- factor(allResults$passive.flow)
      pTitle <- "Flow"
   }
   else {
      allResults <- loadResults(paste(sep="", name, "/active.flow-ReceivedBitRate.data.bz2"))
      pSet   <- factor(allResults$active.flow)
      pTitle <- "Flow"
   }

   numberOfRuns <- length(levels(factor(allResults$Protocol)))
   title <- node

   pdf(paste(sep="", "Results-", name, "-", node, ".pdf"),
       title=title,
       width=20, height=10, family="Helvetica", pointsize=22)

   xTitle <- "Flow #"

   if(node == "passive") {
      ySet   <- allResults$passive.flow.ReceivedBitRate / 1000000
   }
   else {
      ySet   <- allResults$active.flow.ReceivedBitRate / 1000000
   }
   yTitle <- "Application Payload Throughput [Mbit/s]"

   zSet   <- allResults$Scenario
   zTitle <- "Scenario"

   ScenarioBandwdith <- paste(sep="", allResults$Scenario, allResults$QoSBandwidth)


   hset<-data.frame(Flow=pSet, ReceivedBitRate=ySet, ScenarioBandwdith=ScenarioBandwdith)

   p <- ggplot(hset,
           aes(x=Flow,y=ReceivedBitRate,fill=Flow)) +
           scale_fill_manual(values = plotColours)
   p <- p + labs(title=title,
                 fill=zTitle,
                 x=xTitle,
                 y=yTitle)
   # Theme (see http://docs.ggplot2.org/0.9.2.1/theme.html for options):
   p <- p + theme(title           = element_text(size=16),
                  axis.title      = element_text(size=16),
                  strip.text      = element_text(size=16, face="bold"),
                  axis.text.x     = element_text(size=14, angle=90, face="bold", colour="black"),
                  axis.text.y     = element_text(size=14, angle=90, hjust=0.5, colour="black"),
                  legend.title         = element_blank(),
                  #legend.position      = c(1,1),
                  #legend.justification = c(1,1),
                  legend.background    = element_rect(colour = "blue",  fill = "#ffffff", size=1)
                  )
   p <- p + facet_grid(~ScenarioBandwdith) +
            stat_summary(fun=mean, geom='bar', size=3)

   # Add confidence intervals:
   # NOTE: Needs at least 2 (*two*) runs to work!
   if(numberOfRuns >= 2) {
      p <- p + stat_summary(fun.data=mean_cl_boot, geom='pointrange', colour="red")
   }

   # All values as text:
   # p <- p + geom_text(aes(label=sprintf("%1.1f", ReceivedBitRate)),
   #                    vjust=1.5,colour='blue',position=position_dodge(.9),size=6)
   # Only mean value as text:
   p <- p + stat_summary(aes(label=round(..y..,1)), fun=mean, geom="text",
                         colour='blue', size=5, vjust = -0.5)

   print(p)

   dev.off()
}

makePlot("passive")
makePlot("active")
