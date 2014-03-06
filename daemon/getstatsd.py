__author__ = 'pferland'
__email__ = "pferland@randomintervals.com"
__lastedit__ = "2014-03-06"
print "PrinterStats Daemon v2.0 GPL V2.0 ("+ __lastedit__ +") \n\tAuthor: " + __author__ + "\n\tEmail: " + __email__
import sys, re, os
from PrintersConfig import *
from PrinterStatsSQL import *
from PrinterStats import *

folder = os.path.dirname(os.path.realpath(__file__))
print os.path.join(folder+"/config", "printers.ini")
pid = os.getpid()
f = open("/var/run/printerstats.pid", "w")
f.write(str(pid))      # str() converts to string
f.close()

# INI file init, config/config.ini and config/printers.ini
pcfg = PrintersConfig(folder)
config = pcfg.ConfigMap("Daemon")
campuses = pcfg.CampusMap("Campuses")['Campuses'].split(",")
printers = pcfg.ConfigMapPrinters("Printers").get("Printers")
rg = re.compile('(.*?),', re.IGNORECASE | re.DOTALL)

#SQL object init
conn = PrinterStatsSQL(config)
pStats = PrinterStats(conn)
graph = Graphing(conn, config['wwwroot'])

models, printer_campuses, all_hosts = pcfg.generate_hosts_list(conn, campuses, printers)
Model_functions = pStats.create_models_functions(models)

print "Checking Printers table Population."
pStats.check_printers_table(Model_functions, conn, all_hosts)

print "Moving on to the main loop."

while 1:
    for printer in all_hosts:
        print "---------------------"
        host = all_hosts[printer][0]
        model = all_hosts[printer][1]
        printer_id = conn.getprinterid(host)
        campus_name = conn.getprinterscampusname(printer_id)

        supplies = pStats.daemon_get_host_stats(Model_functions, host, model)
        if supplies == -1:
            continue

        conn.setprintervalues(supplies, host, printer_id)

        #Data has been inserted, lets graph it!
