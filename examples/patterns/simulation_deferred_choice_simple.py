from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter, TimeUnit
from simpn.prototypes import task, start_event, end_event, intermediate_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
offer_qeue = shop.add_var("offer queue")
to_choose = shop.add_var("to choose")
processing_queue = shop.add_var("processing queue")
waiting_for_response = shop.add_var("waiting for response")
to_leave = shop.add_var("to leave")
done = shop.add_var("done")

# Define resources.
administrator = shop.add_var("administrator")

administrator.put("a1")

# Define events.
start_event(shop, [], [offer_qeue], "customer_arrived", lambda: exp(1/10))

task(shop, [offer_qeue, administrator], [to_choose, administrator], "create_offer", lambda c, r: [SimToken((c, r), delay=exp(1/4))])

def choose(c):
  waiting_time = exp(1/4)
  if waiting_time < 5:
    return [SimToken((c[0], waiting_time), delay=waiting_time), None]
  else:
    return [None, SimToken((c[0], 5), delay=5)]

shop.add_event([to_choose], [waiting_for_response, to_leave], choose)

intermediate_event(shop, [waiting_for_response], [processing_queue], "wait_for_response", lambda c: [SimToken(c)])

task(shop, [processing_queue, administrator], [done, administrator], "process_response", lambda c,r: [SimToken((c, r), delay=exp(1/4))])

end_event(shop, [done], [], "done")

end_event(shop, [to_leave], [], "left")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_deferred_simple.csv", timeunit=TimeUnit.DAYS)
shop.simulate(24*60, reporter)
reporter.close()
