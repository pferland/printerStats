__author__ = 'pferland'
__email__ = "pferland@randomintervals.com"
__lastedit__ = "2013-12-11"
print "PrinterStats Daemon v2.0 GPL V2.0 (05/12/2013) \n\tAuthor: " + __author__ + "\n\tEmail: " + __email__ + "\n\tLast Edit: " + __lastedit__
import sys, pymysql, re, time
from PrintersConfig import *
from PrinterStatsSQL import *
from PrinterStats import *
from Graphing import *

# INI file init, config/config.ini and config/printers.ini
pcfg = PrintersConfig()
config = pcfg.ConfigMap("Daemon")
campuses = pcfg.CampusMap("Campuses")['Campuses'].split(",")
printers = pcfg.ConfigMapPrinters("Printers").get("Printers")
rg = re.compile('(.*?),', re.IGNORECASE | re.DOTALL)
printer_campuses = []
printer_campus_ids = []
all_hosts = {}
models = []
i = 0

#SQL object init
conn = PrinterStatsSQL(config)
pStats = PrinterStats(conn)
graph = Graphing(conn)

for campus in campuses:
    row = conn.getcampus(campus)
    if row:
        campus_id = row
    else:
        campus_id = conn.setcampusrow(campus)

    campus_printers = rg.findall(printers.get(campus.lower()))
    for printer in campus_printers:
        split = printer.split("|")
        all_hosts[i] = {0: split[0].replace("\n", ""), 1: split[1], 2: campus_id}
        printer_campuses.append(campus)
        i += 1
        if split[1] in models:
            continue
        models.append(split[1])

Model_functions = pStats.create_models_functions(models)

print "Checking Printers table Population."
pStats.check_printers_table(Model_functions, conn, all_hosts)

print "Moving on to the main loop."

while 1:
    for printer in all_hosts:
        print "---------------------"
        host = all_hosts[printer][0]
        model = all_hosts[printer][1]
        printer_id = conn.getprinterid(printer)
        supplies = pStats.daemon_get_host_stats(Model_functions, host, model)
        if supplies == -1:
            continue
        try:
            conn.setprintervalues(supplies, printer_id)
        except StandardError:
            print "Ummm.. something bad happened"
            continue
        #Data has been inserted, lets graph it!
        graphing.gplot(printer_id, printer)