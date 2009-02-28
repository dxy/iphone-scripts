#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2009 Daisuke Yabuki. All Rights Reserved.

"""Generate piecharts re: total # of downloads of iPhone apps.

This quick n' dirty script parses daily report files downloaded from
iTunes connect, calculate total number of downloads (excluding upgrades)
for each application and download piechart(s) drawn with Google Chart API.
"""

__author__ = 'dxy@acm.org (Daisuke Yabuki)'

import os
import sys
import gzip
import urllib2
import optparse

sales = {}

def Usage():
  print "Usage: %s [-D|-W] -s REPORT_FILE_DIRECTORY" % sys.argv[0]


def ParseReportFile(report_file):
  global sales
  report = gzip.open(report_file, 'rb')
  report.readline()
  for line in report:
    entry = line.split('\t')
    title = entry[6]
    product_type_id = entry[8]
    units = int(entry[9])
    date = entry[12]
    country = entry[14]
    #print "%s %s %d %s %s" % (title, product_type_id, units, date, country)

    # ignore upgrades (i.e. product type identifier = 7)
    if product_type_id != '1':
      continue

    if not title in sales:
      # no sales record exists for this app before
      sales[title] = {country: units}
    else:
      # some sales records already exists for this app
      if country in sales[title]:
        # some sales data exists for this app in this country
        current_units = sales[title][country]
      else:
        # just encountering the first sales record for this app in this country
        current_units = 0
      sales[title][country] = current_units + units

  report.close()


def GetReportFileList(directory, use_daily_reports):
  files = os.listdir(directory)
  for file in files:
    if not file.endswith(".txt.gz"):
      continue
    if ((use_daily_reports and file.startswith("S_D_")) or
        (not use_daily_reports and file.startswith("S_W_"))):
      print "processing %s" % file
      ParseReportFile(file)


def DownloadPieChart(application, url, output_directory):
  chart_file = "%s/%s.png" % (output_directory, application)
  req = urllib2.Request(url)
  try:
    response = urllib2.urlopen(req)
  except urllib2.HTTPError, e:
    print e.code, e.msg
    return
  except urllib2.URLError, e:
    print e.code, e.reason
    return
  output = open(chart_file, "wb")
  for data in response:
    output.write(data)
  output.close()


def PreparePieChartRequest(output_directory):
  global sales
  for application in sales:
    print "*** %s: Total downloads by country" % application
    chart_label = ""
    chart_data = ""
    countries = sales[application].keys()
    countries.sort()
    for country in countries:
      print "%s: %d," % (country, sales[application][country]),
      chart_label += "%s|" % country
      chart_data += "%d," % sales[application][country]
    print ""

    # strip the trailing superfluous "," and "|" in order to
    # avoid confusing Chart API
    chart_label = chart_label[:-1]
    chart_data = chart_data[:-1]
    url = ("http://chart.apis.google.com/chart?chs=400x350&cht=p"
           "&chd=t:%s&chl=%s&chtt=%s:+Total+downloads+by+country" %
           (chart_data, chart_label, application))
    #print url
    DownloadPieChart(application, url, output_directory)


def main(argv):
  usage = "Usage: %prog [-D|-W] -s directory"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("-s", "--src-directory", dest="report_directory",
                    metavar="REPORT_FILE_DIRECTORY",
                    help="directory containing downloaded report files")
  parser.add_option("-d", "--dst-directory", dest="output_directory",
                    metavar="IMAGE_OUTPUT_DIRECTORY", default=".",
                    help="directory to generate pie chart images into")
  parser.add_option("-D", "--daily", default=True,
                    action="store_true", dest="use_daily_reports",
                    help="parse daily report files (default)")
  parser.add_option("-W", "--weekly",
                    action="store_false", dest="use_daily_reports",
                    help="parsee weekly report files")

  (options, args) = parser.parse_args()

  if not options.report_directory:
    parser.error("-s option missing")

  GetReportFileList(options.report_directory, options.use_daily_reports)
  PreparePieChartRequest(options.output_directory)


if __name__ == '__main__':
  main(sys.argv[1:])
