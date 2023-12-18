from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter, ProcessReporter
from simpn.prototypes import start_event, task, end_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
waiting = shop.add_var("waiting")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("c1")

# Define events.
start_event(shop, [], [waiting], "arrive", lambda: exp(1/10))

task(shop, [waiting, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

end_event(shop, [done], [], "complete")

# Store the initial state of the simulator.
shop.store_checkpoint("initial state")

# Simulate once with a simple reporter.
reporter = ProcessReporter()
shop.simulate(24*60, reporter)
reporter.print_result()

# Restore the initial state of the simulator, otherwise the next simulation run will continue where the previous run ended.
shop.restore_checkpoint("initial state")

# Simulate once with an EventLogReporter.
reporter = EventLogReporter("./temp/reporting.csv")
shop.simulate(24*60, reporter)
reporter.close()