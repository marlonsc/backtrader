#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import bisect
import collections
import datetime
import itertools
import math
import operator
import sys

import matplotlib
import numpy as np  # guaranteed by matplotlib
import matplotlib.dates as mdates
import matplotlib.font_manager as mfontmgr
import matplotlib.legend as mlegend
import matplotlib.ticker as mticker

from ..analyzers import CAGRAnalyzer
# from matplotlib.gridspec import GridSpec

from ..utils.py3 import range, with_metaclass, string_types, integer_types
from .. import AutoInfoClass, MetaParams, TimeFrame, date2num

from .finance import plot_candlestick, plot_ohlc, plot_volume, plot_lineonclose
from .formatters import (MyVolFormatter, MyDateFormatter, getlocator)
from . import locator as loc
from .multicursor import MultiCursor
from .scheme import PlotScheme
from .utils import tag_box_style


class PInfo(object):
    def __init__(self, sch):
        self.sch = sch
        self.nrows = 0
        self.row = 0
        self.clock = None
        self.x = None
        self.xlen = 0
        self.sharex = None
        self.figs = list()
        self.cursors = list()
        self.daxis = collections.OrderedDict()
        self.vaxis = list()
        self.zorder = dict()
        self.coloridx = collections.defaultdict(lambda: -1)
        self.handles = collections.defaultdict(list)
        self.labels = collections.defaultdict(list)
        self.legpos = collections.defaultdict(int)

        self.prop = mfontmgr.FontProperties(size=self.sch.subtxtsize)

    def newfig(self, figid, numfig, mpyplot):
        fig = mpyplot.figure(figid + numfig)
        self.figs.append(fig)
        self.daxis = collections.OrderedDict()
        self.vaxis = list()
        self.row = 0
        self.sharex = None
        return fig

    def nextcolor(self, ax):
        self.coloridx[ax] += 1
        return self.coloridx[ax]

    def color(self, ax):
        return self.sch.color(self.coloridx[ax])

    def zordernext(self, ax):
        z = self.zorder[ax]
        if self.sch.zdown:
            return z * 0.9999
        return z * 1.0001

    def zordercur(self, ax):
        return self.zorder[ax]


class Plot_OldSync(with_metaclass(MetaParams, object)):
    params = (('scheme', PlotScheme()),
            ('spread', False),  # 添加spread参数
                      )

    def __init__(self, **kwargs):


        if 'spread' in kwargs:
            self.p.spread = kwargs.pop('spread')  # 使用self.p.spread而不是self.spread
            
        for pname, pvalue in kwargs.items():
            setattr(self.p.scheme, pname, pvalue)
            
        if not hasattr(self.p.scheme, 'locbg'):
            setattr(self.p.scheme, 'locbg', 'white')
            setattr(self.p.scheme, 'locbgother', 'white')

    def drawtag(self, ax, x, y, facecolor, edgecolor, alpha=0.9, **kwargs):

        txt = ax.text(x, y, '%.2f' % y, va='center', ha='left',
                      fontsize=self.pinf.sch.subtxtsize,
                      bbox=dict(boxstyle=tag_box_style,
                                facecolor=facecolor,
                                edgecolor=edgecolor,
                                alpha=alpha),
                      # 3.0 is the minimum default for text
                      zorder=self.pinf.zorder[ax] + 3.0,
                      **kwargs)

    def plot(self, strategy, figid=0, numfigs=1, iplot=True,
             start=None, end=None, **kwargs):
        # pfillers={}):
        if not strategy.datas:
            return

        if not len(strategy):
            return

        if iplot:
            if 'ipykernel' in sys.modules:
                matplotlib.use('nbagg')

        # this import must not happen before matplotlib.use
        import matplotlib.pyplot as mpyplot
        self.mpyplot = mpyplot

        self.pinf = PInfo(self.p.scheme)
        if self.p.spread:
            # 备份原始数据
            original_datas = strategy.datas
            
            try:
                # 创建只包含spread的临时列表
                spread_data = [data for data in strategy.datas if data._name == 'spread']
                if not spread_data:
                    raise ValueError("No spread data found")
                
                # 替换datas列表
                strategy.datas = spread_data
                
                # 执行排序和计算
                self.sortdataindicators(strategy)
                self.calcrows(strategy)
                
            finally:
                # 恢复原始数据
                strategy.datas = original_datas
        else:
            # 正常模式
            self.sortdataindicators(strategy)
            self.calcrows(strategy)

        st_dtime = strategy.lines.datetime.plot()
        if start is None:
            start = 0
        if end is None:
            end = len(st_dtime)

        if isinstance(start, datetime.date):
            start = bisect.bisect_left(st_dtime, date2num(start))

        if isinstance(end, datetime.date):
            end = bisect.bisect_right(st_dtime, date2num(end))

        if end < 0:
            end = len(st_dtime) + 1 + end  # -1 =  len() -2 = len() - 1

        slen = len(st_dtime[start:end])
        d, m = divmod(slen, numfigs)
        pranges = list()
        for i in range(numfigs):
            a = d * i + start
            if i == (numfigs - 1):
                d += m  # add remainder to last stint
            b = a + d

            pranges.append([a, b, d])

        figs = []

        for numfig in range(numfigs):
            # prepare a figure
            fig = self.pinf.newfig(figid, numfig, self.mpyplot)
            figs.append(fig)

            self.pinf.pstart, self.pinf.pend, self.pinf.psize = pranges[numfig]
            self.pinf.xstart = self.pinf.pstart
            self.pinf.xend = self.pinf.pend

            self.pinf.clock = strategy
            self.pinf.xreal = self.pinf.clock.datetime.plot(
                self.pinf.pstart, self.pinf.psize)
            self.pinf.xlen = len(self.pinf.xreal)
            self.pinf.x = list(range(self.pinf.xlen))
            # self.pinf.pfillers = {None: []}
            # for key, val in pfillers.items():
            #     pfstart = bisect.bisect_left(val, self.pinf.pstart)
            #     pfend = bisect.bisect_right(val, self.pinf.pend)
            #     self.pinf.pfillers[key] = val[pfstart:pfend]

            # Do the plotting
            # Things that go always at the top (observers)
            self.pinf.xdata = self.pinf.x
            for ptop in self.dplotstop:
                self.plotind(None, ptop, subinds=self.dplotsover[ptop])

            # Create the rest on a per data basis
            dt0, dt1 = self.pinf.xreal[0], self.pinf.xreal[-1]
            for data in strategy.datas:

                # spread 模式下只绘制spread
                if self.p.spread and data._name != 'spread':
                    continue

                if not data.plotinfo.plot:
                    continue

                self.pinf.xdata = self.pinf.x
                xd = data.datetime.plotrange(self.pinf.xstart, self.pinf.xend)
                if len(xd) < self.pinf.xlen:
                    self.pinf.xdata = xdata = []
                    xreal = self.pinf.xreal
                    dts = data.datetime.plot()
                    xtemp = list()
                    for dt in (x for x in dts if dt0 <= x <= dt1):
                        dtidx = bisect.bisect_left(xreal, dt)
                        xdata.append(dtidx)
                        xtemp.append(dt)

                    self.pinf.xstart = bisect.bisect_left(dts, xtemp[0])
                    self.pinf.xend = bisect.bisect_right(dts, xtemp[-1])


                self.plotdata(data, self.dplotsover[data])

                for ind in self.dplotsup[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])




            cursor = MultiCursor(
                fig.canvas, list(self.pinf.daxis.values()),
                useblit=True,
                horizOn=True, vertOn=True,
                horizMulti=False, vertMulti=True,
                horizShared=True, vertShared=False,
                color='black', lw=1, ls=':')

            self.pinf.cursors.append(cursor)

            # Put the subplots as indicated by hspace
            fig.subplots_adjust(hspace=self.pinf.sch.plotdist,
                                top=0.98, left=0.05, bottom=0.05, right=0.95)

            laxis = list(self.pinf.daxis.values())

            # Find last axis which is not a twinx (date locator fails there)
            i = -1
            while True:
                lastax = laxis[i]
                if lastax not in self.pinf.vaxis:
                    break

                i -= 1

            self.setlocators(lastax)  # place the locators/fmts

            # Applying fig.autofmt_xdate if the data axis is the last one
            # breaks the presentation of the date labels. why?
            # Applying the manual rotation with setp cures the problem
            # but the labels from all axis but the last have to be hidden
            for ax in laxis:
                self.mpyplot.setp(ax.get_xticklabels(), visible=False)

            self.mpyplot.setp(lastax.get_xticklabels(), visible=True,
                              rotation=self.pinf.sch.tickrotation)

            # Things must be tight along the x axis (to fill both ends)
            axtight = 'x' if not self.pinf.sch.ytight else 'both'
            self.mpyplot.autoscale(enable=True, axis=axtight, tight=True)

        return figs

    def setlocators(self, ax):
        clock = sorted(self.pinf.clock.datas,
                       key=lambda x: (x._timeframe, x._compression))[0]

        comp = getattr(clock, '_compression', 1)
        tframe = getattr(clock, '_timeframe', TimeFrame.Days)

        if self.pinf.sch.fmt_x_data is None:
            if tframe == TimeFrame.Years:
                fmtdata = '%Y'
            elif tframe == TimeFrame.Months:
                fmtdata = '%Y-%m'
            elif tframe == TimeFrame.Weeks:
                fmtdata = '%Y-%m-%d'
            elif tframe == TimeFrame.Days:
                fmtdata = '%Y-%m-%d'
            elif tframe == TimeFrame.Minutes:
                fmtdata = '%Y-%m-%d %H:%M'
            elif tframe == TimeFrame.Seconds:
                fmtdata = '%Y-%m-%d %H:%M:%S'
            elif tframe == TimeFrame.MicroSeconds:
                fmtdata = '%Y-%m-%d %H:%M:%S.%f'
            elif tframe == TimeFrame.Ticks:
                fmtdata = '%Y-%m-%d %H:%M:%S.%f'
        else:
            fmtdata = self.pinf.sch.fmt_x_data

        fordata = MyDateFormatter(self.pinf.xreal, fmt=fmtdata)
        for dax in self.pinf.daxis.values():
            dax.fmt_xdata = fordata

        # Major locator / formatter
        locmajor = loc.AutoDateLocator(self.pinf.xreal)
        ax.xaxis.set_major_locator(locmajor)
        if self.pinf.sch.fmt_x_ticks is None:
            autofmt = loc.AutoDateFormatter(self.pinf.xreal, locmajor)
        else:
            autofmt = MyDateFormatter(self.pinf.xreal,
                                      fmt=self.pinf.sch.fmt_x_ticks)
        ax.xaxis.set_major_formatter(autofmt)

    def calcrows(self, strategy):
        # Calculate the total number of rows
        rowsmajor = self.pinf.sch.rowsmajor
        rowsminor = self.pinf.sch.rowsminor
        nrows = 0

        datasnoplot = 0
        for data in strategy.datas:
            if not data.plotinfo.plot:
                # neither data nor indicators nor volume add rows
                datasnoplot += 1
                self.dplotsup.pop(data, None)
                self.dplotsdown.pop(data, None)
                self.dplotsover.pop(data, None)

            else:
                pmaster = data.plotinfo.plotmaster
                if pmaster is data:
                    pmaster = None
                if pmaster is not None:
                    # data doesn't add a row, but volume may
                    if self.pinf.sch.volume:
                        nrows += rowsminor
                else:
                    # data adds rows, volume may
                    nrows += rowsmajor
                    if self.pinf.sch.volume and not self.pinf.sch.voloverlay:
                        nrows += rowsminor

        if False:
            # Datas and volumes
            nrows += (len(strategy.datas) - datasnoplot) * rowsmajor
            if self.pinf.sch.volume and not self.pinf.sch.voloverlay:
                nrows += (len(strategy.datas) - datasnoplot) * rowsminor

        # top indicators/observers
        nrows += len(self.dplotstop) * rowsminor

        # indicators above datas
        nrows += sum(len(v) for v in self.dplotsup.values())
        nrows += sum(len(v) for v in self.dplotsdown.values())

        self.pinf.nrows = nrows

    def newaxis(self, obj, rowspan):
        ax = self.mpyplot.subplot2grid(
            (self.pinf.nrows, 1), (self.pinf.row, 0),
            rowspan=rowspan, sharex=self.pinf.sharex)

        # update the sharex information if not available
        if self.pinf.sharex is None:
            self.pinf.sharex = ax

        # update the row index with the taken rows
        self.pinf.row += rowspan

        # save the mapping indicator - axis and return
        self.pinf.daxis[obj] = ax

        # Activate grid in all axes if requested
        ax.yaxis.tick_right()
        ax.grid(self.pinf.sch.grid, which='both')

        return ax

    def plotind(self, iref, ind,
                subinds=None, upinds=None, downinds=None,
                masterax=None):

        sch = self.p.scheme

        # check subind
        subinds = subinds or []
        upinds = upinds or []
        downinds = downinds or []

        # plot subindicators on self with independent axis above
        for upind in upinds:
            self.plotind(iref, upind)

        # Get an axis for this plot
        ax = masterax or self.newaxis(ind, rowspan=self.pinf.sch.rowsminor)

        indlabel = ind.plotlabel()

        # Scan lines quickly to find out if some lines have to be skipped for
        # legend (because matplotlib reorders the legend)
        toskip = 0
        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)
            lineplotinfo = getattr(ind.plotlines, '_%d' % lineidx, None)
            if not lineplotinfo:
                lineplotinfo = getattr(ind.plotlines, linealias, None)
            if not lineplotinfo:
                lineplotinfo = AutoInfoClass()
            pltmethod = lineplotinfo._get('_method', 'plot')
            if pltmethod != 'plot':
                toskip += 1 - lineplotinfo._get('_plotskip', False)

        if toskip >= ind.size():
            toskip = 0

        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)

            lineplotinfo = getattr(ind.plotlines, '_%d' % lineidx, None)
            if not lineplotinfo:
                lineplotinfo = getattr(ind.plotlines, linealias, None)

            if not lineplotinfo:
                lineplotinfo = AutoInfoClass()

            if lineplotinfo._get('_plotskip', False):
                continue

            # Legend label only when plotting 1st line
            if masterax and not ind.plotinfo.plotlinelabels:
                label = indlabel * (not toskip) or '_nolegend'
            else:
                label = (indlabel + '\n') * (not toskip)
                label += lineplotinfo._get('_name', '') or linealias

            toskip -= 1  # one line less until legend can be added

            # plot data
            lplot = line.plotrange(self.pinf.xstart, self.pinf.xend)

            # Global and generic for indicator
            if self.pinf.sch.linevalues and ind.plotinfo.plotlinevalues:
                plotlinevalue = lineplotinfo._get('_plotvalue', True)
                if plotlinevalue and not math.isnan(lplot[-1]):
                    label += ' %.2f' % lplot[-1]

            plotkwargs = dict()
            linekwargs = lineplotinfo._getkwargs(skip_=True)

            if linekwargs.get('color', None) is None:
                if not lineplotinfo._get('_samecolor', False):
                    self.pinf.nextcolor(ax)
                plotkwargs['color'] = self.pinf.color(ax)

            plotkwargs.update(dict(aa=True, label=label))
            plotkwargs.update(**linekwargs)

            if ax in self.pinf.zorder:
                plotkwargs['zorder'] = self.pinf.zordernext(ax)

            pltmethod = getattr(ax, lineplotinfo._get('_method', 'plot'))


            xdata, lplotarray = self.pinf.xdata, lplot
            if lineplotinfo._get('_skipnan', False):
                # Get the full array and a mask to skipnan
                lplotarray = np.array(lplot)
                lplotmask = np.isfinite(lplotarray)

                # Get both the axis and the data masked
                lplotarray = lplotarray[lplotmask]
                xdata = np.array(xdata)[lplotmask]

  

            plottedline = pltmethod(xdata, lplotarray, **plotkwargs)
            try:
                plottedline = plottedline[0]
            except:
                # Possibly a container of artists (when plotting bars)
                pass

            self.pinf.zorder[ax] = plottedline.get_zorder()

            vtags = lineplotinfo._get('plotvaluetags', True)
            if self.pinf.sch.valuetags and vtags:
                linetag = lineplotinfo._get('_plotvaluetag', True)
                if linetag and not math.isnan(lplot[-1]):
                    # line has valid values, plot a tag for the last value
                    self.drawtag(ax, len(self.pinf.xreal), lplot[-1],
                                 facecolor=self.pinf.sch.locbgother,
                                 edgecolor=self.pinf.color(ax))

            farts = (('_gt', operator.gt), ('_lt', operator.lt), ('', None),)
            for fcmp, fop in farts:
                fattr = '_fill' + fcmp
                fref, fcol = lineplotinfo._get(fattr, (None, None))
                if fref is not None:
                    y1 = np.array(lplot)
                    if isinstance(fref, integer_types):
                        y2 = np.full_like(y1, fref)
                    else:  # string, naming a line, nothing else is supported
                        l2 = getattr(ind, fref)
                        prl2 = l2.plotrange(self.pinf.xstart, self.pinf.xend)
                        y2 = np.array(prl2)
                    kwargs = dict()
                    if fop is not None:
                        kwargs['where'] = fop(y1, y2)

                    falpha = self.pinf.sch.fillalpha
                    if isinstance(fcol, (list, tuple)):
                        fcol, falpha = fcol

                    ax.fill_between(self.pinf.xdata, y1, y2,
                                    facecolor=fcol,
                                    alpha=falpha,
                                    interpolate=True,
                                    **kwargs)

        # plot subindicators that were created on self
        for subind in subinds:
            self.plotind(iref, subind, subinds=self.dplotsover[subind],
                         masterax=ax)

        if not masterax:
            # adjust margin if requested ... general of particular
            ymargin = ind.plotinfo._get('plotymargin', 0.0)
            ymargin = max(ymargin, self.pinf.sch.yadjust)
            if ymargin:
                ax.margins(y=ymargin)

            # Set specific or generic ticks
            yticks = ind.plotinfo._get('plotyticks', [])
            if not yticks:
                yticks = ind.plotinfo._get('plotyhlines', [])

            if yticks:
                ax.set_yticks(yticks)
            else:
                locator = mticker.MaxNLocator(nbins=4, prune='both')
                ax.yaxis.set_major_locator(locator)

            # Set specific hlines if asked to
            hlines = ind.plotinfo._get('plothlines', [])
            if not hlines:
                hlines = ind.plotinfo._get('plotyhlines', [])
            for hline in hlines:
                ax.axhline(hline, color=self.pinf.sch.hlinescolor,
                           ls=self.pinf.sch.hlinesstyle,
                           lw=self.pinf.sch.hlineswidth)

            if self.pinf.sch.legendind and \
               ind.plotinfo._get('plotlegend', True):

                handles, labels = ax.get_legend_handles_labels()
                # Ensure that we have something to show
                if labels:
                    # location can come from the user
                    loc = ind.plotinfo.legendloc or self.pinf.sch.legendindloc

                    # Legend done here to ensure it includes all plots
                    legend = ax.legend(loc=loc,
                                       numpoints=1, frameon=False,
                                       shadow=False, fancybox=False,
                                       prop=self.pinf.prop)

                    # legend.set_title(indlabel, prop=self.pinf.prop)
                    # hack: if title is set. legend has a Vbox for the labels
                    # which has a default "center" set
                    legend._legend_box.align = 'left'

        # plot subindicators on self with independent axis below
        for downind in downinds:
            self.plotind(iref, downind)

    def plotvolume(self, data, opens, highs, lows, closes, volumes, label):
        pmaster = data.plotinfo.plotmaster
        if pmaster is data:
            pmaster = None
        voloverlay = (self.pinf.sch.voloverlay and pmaster is None)

        # if sefl.pinf.sch.voloverlay:
        if voloverlay:
            rowspan = self.pinf.sch.rowsmajor
        else:
            rowspan = self.pinf.sch.rowsminor

        ax = self.newaxis(data.volume, rowspan=rowspan)

        # if self.pinf.sch.voloverlay:
        if voloverlay:
            volalpha = self.pinf.sch.voltrans
        else:
            volalpha = 1.0

        maxvol = volylim = max(volumes)
        if maxvol:

            # Plot the volume (no matter if as overlay or standalone)
            vollabel = label
            volplot, = plot_volume(ax, self.pinf.xdata, opens, closes, volumes,
                                   colorup=self.pinf.sch.volup,
                                   colordown=self.pinf.sch.voldown,
                                   alpha=volalpha, label=vollabel)

            nbins = 6
            prune = 'both'
            # if self.pinf.sch.voloverlay:
            if voloverlay:
                # store for a potential plot over it
                nbins = int(nbins / self.pinf.sch.volscaling)
                prune = None

                volylim /= self.pinf.sch.volscaling
                ax.set_ylim(0, volylim, auto=True)
            else:
                # plot a legend
                handles, labels = ax.get_legend_handles_labels()
                if handles:

                    # location can come from the user
                    loc = data.plotinfo.legendloc or self.pinf.sch.legendindloc

                    # Legend done here to ensure it includes all plots
                    legend = ax.legend(loc=loc,
                                       numpoints=1, frameon=False,
                                       shadow=False, fancybox=False,
                                       prop=self.pinf.prop)

            locator = mticker.MaxNLocator(nbins=nbins, prune=prune)
            ax.yaxis.set_major_locator(locator)
            ax.yaxis.set_major_formatter(MyVolFormatter(maxvol))

        if not maxvol:
            ax.set_yticks([])
            return None

        return volplot

    def plotdata(self, data, indicators):
        for ind in indicators:
            upinds = self.dplotsup[ind]
            for upind in upinds:
                self.plotind(data, upind,
                             subinds=self.dplotsover[upind],
                             upinds=self.dplotsup[upind],
                             downinds=self.dplotsdown[upind])

        opens = data.open.plotrange(self.pinf.xstart, self.pinf.xend)
        highs = data.high.plotrange(self.pinf.xstart, self.pinf.xend)
        lows = data.low.plotrange(self.pinf.xstart, self.pinf.xend)
        closes = data.close.plotrange(self.pinf.xstart, self.pinf.xend)
        volumes = data.volume.plotrange(self.pinf.xstart, self.pinf.xend)

        vollabel = 'Volume'
        pmaster = data.plotinfo.plotmaster
        if pmaster is data:
            pmaster = None

        datalabel = ''
        if hasattr(data, '_name') and data._name:
            datalabel += data._name

        voloverlay = (self.pinf.sch.voloverlay and pmaster is None)

        if not voloverlay:
            vollabel += ' ({})'.format(datalabel)

        # if self.pinf.sch.volume and self.pinf.sch.voloverlay:
        axdatamaster = None
        if self.pinf.sch.volume and voloverlay:
            volplot = self.plotvolume(
                data, opens, highs, lows, closes, volumes, vollabel)
            axvol = self.pinf.daxis[data.volume]
            ax = axvol.twinx()
            self.pinf.daxis[data] = ax
            self.pinf.vaxis.append(ax)
        else:
            if pmaster is None:
                ax = self.newaxis(data, rowspan=self.pinf.sch.rowsmajor)
            elif getattr(data.plotinfo, 'sameaxis', False):
                axdatamaster = self.pinf.daxis[pmaster]
                ax = axdatamaster
            else:
                axdatamaster = self.pinf.daxis[pmaster]
                ax = axdatamaster.twinx()
                self.pinf.vaxis.append(ax)

        if hasattr(data, '_compression') and \
           hasattr(data, '_timeframe'):
            tfname = TimeFrame.getname(data._timeframe, data._compression)
            datalabel += ' (%d %s)' % (data._compression, tfname)

        plinevalues = getattr(data.plotinfo, 'plotlinevalues', True)
        if self.pinf.sch.style.startswith('line'):
            if self.pinf.sch.linevalues and plinevalues:
                datalabel += ' C:%.2f' % closes[-1]

            if axdatamaster is None:
                color = self.pinf.sch.loc
            else:
                self.pinf.nextcolor(axdatamaster)
                color = self.pinf.color(axdatamaster)

            plotted = plot_lineonclose(
                ax, self.pinf.xdata, closes,
                color=color, label=datalabel)
        else:
            if self.pinf.sch.linevalues and plinevalues:
                datalabel += ' O:%.2f H:%.2f L:%.2f C:%.2f' % \
                             (opens[-1], highs[-1], lows[-1], closes[-1])
            if self.pinf.sch.style.startswith('candle'):
                plotted = plot_candlestick(
                    ax, self.pinf.xdata, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel,
                    alpha=self.pinf.sch.baralpha,
                    fillup=self.pinf.sch.barupfill,
                    filldown=self.pinf.sch.bardownfill)

            elif self.pinf.sch.style.startswith('bar') or True:
                # final default option -- should be "else"
                plotted = plot_ohlc(
                    ax, self.pinf.xdata, opens, highs, lows, closes,
                    colorup=self.pinf.sch.barup,
                    colordown=self.pinf.sch.bardown,
                    label=datalabel)

        self.pinf.zorder[ax] = plotted[0].get_zorder()

        # Code to place a label at the right hand side with the last value
        vtags = data.plotinfo._get('plotvaluetags', True)
        if self.pinf.sch.valuetags and vtags:
            self.drawtag(ax, len(self.pinf.xreal), closes[-1],
                         facecolor=self.pinf.sch.locbg,
                         edgecolor=self.pinf.sch.loc)

        ax.yaxis.set_major_locator(mticker.MaxNLocator(prune='both'))
        # make sure "over" indicators do not change our scale
        if data.plotinfo._get('plotylimited', True):
            if axdatamaster is None:
                ax.set_ylim(ax.get_ylim())

        if self.pinf.sch.volume:
            # if not self.pinf.sch.voloverlay:
            if not voloverlay:
                self.plotvolume(
                    data, opens, highs, lows, closes, volumes, vollabel)
            else:
                # Prepare overlay scaling/pushup or manage own axis
                if self.pinf.sch.volpushup:
                    # push up overlaid axis by lowering the bottom limit
                    axbot, axtop = ax.get_ylim()
                    axbot *= (1.0 - self.pinf.sch.volpushup)
                    ax.set_ylim(axbot, axtop)

        for ind in indicators:

            self.plotind(data, ind, subinds=self.dplotsover[ind], masterax=ax)


        handles, labels = ax.get_legend_handles_labels()
        a = axdatamaster or ax
        if handles:
            # put data and volume legend entries in the 1st positions
            # because they are "collections" they are considered after Line2D
            # for the legend entries, which is not our desire
            # if self.pinf.sch.volume and self.pinf.sch.voloverlay:

            ai = self.pinf.legpos[a]
            if self.pinf.sch.volume and voloverlay:
                if volplot:
                    # even if volume plot was requested, there may be no volume
                    labels.insert(ai, vollabel)
                    handles.insert(ai, volplot)

            didx = labels.index(datalabel)
            labels.insert(ai, labels.pop(didx))
            handles.insert(ai, handles.pop(didx))

            if axdatamaster is None:
                self.pinf.handles[ax] = handles
                self.pinf.labels[ax] = labels
            else:
                self.pinf.handles[axdatamaster] = handles
                self.pinf.labels[axdatamaster] = labels
                # self.pinf.handles[axdatamaster].extend(handles)
                # self.pinf.labels[axdatamaster].extend(labels)

            h = self.pinf.handles[a]
            l = self.pinf.labels[a]

            axlegend = a
            loc = data.plotinfo.legendloc or self.pinf.sch.legenddataloc
            legend = axlegend.legend(h, l,
                                     loc=loc,
                                     frameon=False, shadow=False,
                                     fancybox=False, prop=self.pinf.prop,
                                     numpoints=1, ncol=1)

            # hack: if title is set. legend has a Vbox for the labels
            # which has a default "center" set
            legend._legend_box.align = 'left'

        for ind in indicators:
            downinds = self.dplotsdown[ind]
            for downind in downinds:
                self.plotind(data, downind,
                             subinds=self.dplotsover[downind],
                             upinds=self.dplotsup[downind],
                             downinds=self.dplotsdown[downind])

        self.pinf.legpos[a] = len(self.pinf.handles[a])

        if data.plotinfo._get('plotlog', False):
            a = axdatamaster or ax
            a.set_yscale('log')

    def show(self):
        self.mpyplot.show()

    def savefig(self, fig, filename, width=16, height=9, dpi=300, tight=True):
        fig.set_size_inches(width, height)
        bbox_inches = 'tight' * tight or None
        fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches)

    def sortdataindicators(self, strategy):
        # These lists/dictionaries hold the subplots that go above each data
        self.dplotstop = list()
        self.dplotsup = collections.defaultdict(list)
        self.dplotsdown = collections.defaultdict(list)
        self.dplotsover = collections.defaultdict(list)

        # Sort observers in the different lists/dictionaries
        for x in strategy.getobservers():
            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            if x.plotinfo.subplot:
                self.dplotstop.append(x)
            else:
                key = getattr(x._clock, 'owner', x._clock)
                self.dplotsover[key].append(x)

        # Sort indicators in the different lists/dictionaries
        for x in strategy.getindicators():
            if not hasattr(x, 'plotinfo'):
                # no plotting support - so far LineSingle derived classes
                continue

            if not x.plotinfo.plot or x.plotinfo.plotskip:
                continue

            x._plotinit()  # will be plotted ... call its init function

            # support LineSeriesStub which has "owner" to point to the data
            key = getattr(x._clock, 'owner', x._clock)
            if key is strategy:  # a LinesCoupler
                key = strategy.data

            if getattr(x.plotinfo, 'plotforce', False):
                if key not in strategy.datas:
                    datas = strategy.datas
                    while True:
                        if key not in strategy.datas:
                            key = key._clock
                        else:
                            break

            xpmaster = x.plotinfo.plotmaster
            if xpmaster is x:
                xpmaster = None
            if xpmaster is not None:
                key = xpmaster

            if x.plotinfo.subplot and xpmaster is None:
                if x.plotinfo.plotabove:
                    self.dplotsup[key].append(x)
                else:
                    self.dplotsdown[key].append(x)
            else:
                self.dplotsover[key].append(x)


# class CustomPlot(Plot_OldSync):
#     def plot(self, strategy, figid=0, numfigs=1, iplot=True, start=None, end=None, **kwargs):
#         # 1) 调用父类的 plot 方法，先画出原版图像
#         super().plot(strategy, figid=figid, numfigs=numfigs,
#                      iplot=iplot, start=start, end=end, **kwargs)
        
#         # 2) 获取当前 Figure
#         fig = self.mpyplot.figure(figid)
#         axes = fig.get_axes()
#         if not axes:
#             return  # 没有子图就不继续
#         # 自定义 Gridspec, 1行2列, 比例比如[3,1]代表第一列占3份, 第二列占1份
#         gs = GridSpec(1, 2, figure=fig, width_ratios=[3, 1])

        
#         # 3) 在右侧新增一个子图，用于显示 Spread
#         ax_spread = fig.add_subplot(1, 2, 2, sharex=axes[0])  # 1行2列，右边第2个
#         ax_spread.set_ylabel('Spread')

#         # 4) OldSync 模式下，需要使用 self.pinf 中的 pstart / psize 来获取可见区间
#         pstart = self.pinf.pstart
#         psize = self.pinf.psize
#         pstop = pstart + psize  # 可见区间结束

#         # 5) 获取时间轴 self.pinf.x，长度为 psize
#         #    self.pinf.x 通常是 range(pstart, pstop) => 做了映射
#         xvals = self.pinf.x  # xvals的长度应是 psize

#         # ============== 绘制 Spread (Indicator) ==============
#         # 假设你的策略里有 strategy.spread = SomeIndicator(...)
#         # 并且 lines.spread 里存放了价差数据
#         spread_line = strategy.spread.lines.spread

#         # 创建一个同等长度的数组来存放 y 值
#         spread_data = [np.nan] * psize

#         # OldSync 的“倒序”取值方式:
#         #   最新 bar => line[0]
#         #   往前 1 根 => line[-1], 往前 n 根 => line[-n]
#         #   i 从 pstart .. pstop-1，ago = pstop - 1 - i
#         for i in range(pstart, pstop):
#             ago = (pstop - 1) - i
#             if ago < len(spread_line):
#                 spread_data[i - pstart] = spread_line[-(ago + 1)]

#         # 用 matplotlib 画出这条 spread 曲线
#         ax_spread.plot(xvals, spread_data, label='Spread', color='blue')

#         # ============== 绘制买卖信号 (若仍是 Indicator) ==============
#         # 如果 strategy.buy_signal / strategy.sell_signal 也是 Indicator lines
#         # 则同理用倒序索引来取布尔值(或数值)
#         # 下面只是一个示例，如果 buy_signal/sell_signal 不是这样实现，请自行修改

#         # -- 买点 --
#         if hasattr(strategy, 'buy_signal'):
#             buy_line = strategy.buy_signal.lines[0]  # 假设是单线
#             buy_idx = []  # 保存在可见区间内为 True 的索引
#             for i in range(pstart, pstop):
#                 ago = (pstop - 1) - i
#                 if ago < len(buy_line):
#                     if buy_line[-(ago + 1)]:
#                         buy_idx.append(i - pstart)

#             # 在 buy_idx 对应的 xvals/yvals 处画 '^'
#             # yvals 就用 spread_data 对应的值
#             bx = [xvals[idx] for idx in buy_idx]
#             by = [spread_data[idx] for idx in buy_idx]
#             ax_spread.plot(bx, by, 'g^', markersize=8, label='Buy')

#         # -- 卖点 --
#         if hasattr(strategy, 'sell_signal'):
#             sell_line = strategy.sell_signal.lines[0]
#             sell_idx = []
#             for i in range(pstart, pstop):
#                 ago = (pstop - 1) - i
#                 if ago < len(sell_line):
#                     if sell_line[-(ago + 1)]:
#                         sell_idx.append(i - pstart)

#             sx = [xvals[idx] for idx in sell_idx]
#             sy = [spread_data[idx] for idx in sell_idx]
#             ax_spread.plot(sx, sy, 'rv', markersize=8, label='Sell')

#         ax_spread.legend(loc='best')

#         # 6) 同步 x 轴
#         ax_spread.set_xlim(axes[0].get_xlim())
#         fig.subplots_adjust(wspace=0.2)  # 调整子图之间的间距


#         # 7) 调整布局
#         fig.subplots_adjust(wspace=0.2)

# class CustomPlot(Plot_OldSync):
#     def __init__(self, ** kwargs):
#         super().__init__(**kwargs)
#         # 新增独立绘图标识
#         self.cumulative_ax = None
#
#     def calcrows(self, strategy):
#         super().calcrows(strategy)
#         # 强制为累计收益保留独立行空间
#         self.pinf.nrows += max(3, self.pinf.sch.rowsminor)  # 最小3行高度
#
#     def plot(self, strategy, figid=0, numfigs=1, iplot=True,  ** kwargs):
#         # 调用父类方法绘制基础图表
#         figs = super().plot(strategy, figid, numfigs, iplot,  ** kwargs)
#
#         # 获取累计收益分析器
#         cagr_analyzer = next((a for a in strategy.analyzers
#                               if isinstance(a, CAGRAnalyzer)), None)
#         if not cagr_analyzer:
#             return figs
#
#         for fig in figs:
#
#         #     # 创建独立坐标系（关键修改点）
#             grid = (self.pinf.nrows, 1)
#             self.pinf.row = self.pinf.nrows - self.pinf.sch.rowsminor  # 定位到最后几行
#             ax = self.newaxis('cumulative', rowspan=self.pinf.sch.rowsminor)
#         #
#         # # 初始化坐标系参数
#             self.pinf.zorder[ax] = 2.0  # 确保在其它元素上层
#         # ax.set_ylabel('Cumulative Return', rotation=90)
#         #
#         # # 同步主图时间轴
#             ax.sharex(self.pinf.sharex)
#         #
#         # # 转换时间戳
#         # dates = [date2num(d) for d in cagr_analyzer.dates]
#         #
#             # # 绘制累计收益曲线
#             main_line, = ax.plot(dates, cagr_analyzer.cum_returns,
#                                  color='#2ca02c',  # 使用醒目颜色
#                                  linewidth=2,
#                                  label='Cumulative Return')
#         #
#         #     # # 添加最终数值标签
#         #     # if len(cagr_analyzer.cum_returns) > 0:
#         #     #     last_val = cagr_analyzer.cum_returns[-1]
#         #     #     self.drawtag(ax, len(dates), last_val,
#         #     #                  facecolor='#d62728',  # 红色背景
#         #     #                  edgecolor='black',
#         #     #                  alpha=0.9)
#         #     #
#         # # 强制刷新布局
#         # figs.subplots_adjust(
#         #     hspace=0.3,  # 增加行间距
#         #     top=0.95 - (0.05 * self.pinf.sch.rowsminor)  # 动态调整顶部间距
#         # )
#
#         return figs
plot=Plot_OldSync
# plot=CustomPlot
