import inspect
from sortedcontainers import SortedList


class SimVar:
    """
    A simulation variable SimVar has an identifier and a marking.
    A simulation variable can have multiple values. These values are available at particular times.
    For example, a variable van have the value 1 at time 0 (denoted as 1@0) and also 2@0.
    These values are also called tokens. Multiple tokens are called a marking of the variable.
    The marking is represented as:

     - a dictionary marking_count of tokens -> the number of each token.
       For example, {1@0: 1, 2@0: 1} represents the situation above, in which there is one token
       with value 1 at time 0 and one with value 2 at time 0.
     - a sorted list marking_order of tokens, which keeps tokens in the order of their timestamp.

     The functions put and remove, put and remove tokens in such a way that the marking_count and marking_order are maintained.

    :param _id: the identifier of the SimVar.
    """

    def __init__(self, _id):
        self._id = _id
        self.marking_count = dict()
        self.marking_order = SortedList(key=lambda token: token.time)

    def put(self, value, time=0):
        """
        Put a token value in the SimVar at a particular time.

        :param value: the value to put in the SimVar.
        :param time: the time to make this value available at.
        """
        token = SimToken(value, time)
        self.add_token(token)

    def add_token(self, token, count=1):
        """
        Adds a token value in the SimVar.

        :param token: the token value to put in the SimVar.
        :param count: the number of times to put the token value in the SimVar (defaults to 1 time).
        """
        if token not in self.marking_count:
            self.marking_count[token] = count
            self.marking_order.add(token)
        else:
            self.marking_count[token] += count

    def remove_token(self, token):
        """
        Removes a token value (once) from the SimVar.

        :param token: the token value to remove from the SimVar.
        """
        if token in self.marking_count:
            self.marking_count[token] -= 1
        else:
            raise LookupError("No token '" + token + "' at place '" + str(self) + "'.")
        if self.marking_count[token] == 0:
            del self.marking_count[token]
            self.marking_order.remove(token)

    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()


class SimEvent:
    """
    A simulation event SimEvent that can happen when tokens are available on all of its
    incoming SimVar and its guard evaluates to True. When it happens, it consumes a token from each
    of its incoming SimVar and produces a token on each of its outgoing places according to `behavior`.
    The behavior takes just the values of the SimVar as input, but produces tokens as output: values with a delay.
    The delay can also be 0, meaning the token is produced with 0 delay.
    For example, consider the event with `incoming` `SimVar` [a, b] that have 2@1 and 2@1.
    The event has `outgoing` `SimVar` [c, d], behavior lambda a, b: [(a + b)@+1, (a - b)@+2].
    This event can happen for a = 2@1 and b = 2@1. Thus, it will happen at time 1, generating
    [3@+1, 1@+2] according to its behavior. Therefore, after the event has happened, c and d
    will have the tokens 3@2 and 1@3.

    :param _id: the identifier of the event.
    :param incoming: a list of incoming SimVar of the event.
    :param outgoing: a list of outgoing SimVar of the event
    :param guard: a function that takes as many parameters as there are incoming SimVar. The function must evaluate to True or False for all possible values of SimVar. The event can only happen for values for which the guard function evaluates to True.
    :param behavior: a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many elements as there are outgoing SimVar. The elements must be tokens that carry the resulting values and the delay with which these values become available. When the event happens, the function is performed on the incoming SimVar and the result of the function is put on the outgoing SimVar with the corresponding delays.
    """

    def __init__(self, _id, guard=None, behavior=None, incoming=None, outgoing=None):
        self._id = _id
        self.guard = guard
        if incoming is None:
            self.incoming = []
        else:
            self.incoming = incoming
        if outgoing is None:
            self.outgoing = []
        else:
            self.outgoing = outgoing
        self.behavior = behavior

    def set_guard(self, func):
        """
        Set the guard function.

        :param func: a function with as many input parameters as there are incoming SimVar, which generates a list with as many elements as there are outgoing SimVar.
        """
        self.guard = func

    def set_inflow(self, incoming):
        """
        Set the incoming SimVar.

        :param incoming: a list of SimVar.
        """
        self.incoming = incoming

    def set_outflow(self, outgoing):
        """
        Set the outgoing SimVar.

        :param outgoing: a list of SimVar.
        """
        self.outgoing = outgoing

    def get_id(self):
        return self._id

    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()


class SimToken:
    """
    A token SimToken, which is a possible value of a SimVar. A token has a value and the time at which this value is available in a SimVar.
    When the SimToken is used as the return value of a behavior, the time represents the delay with which the value with be available rather than the time.
    The value will then be available at current_time + time.

    :param value: the value of the token.
    :param time: the time at which the value is available. When used as the return of a event behavior, the value represents the delay. The token will then be available as current_time + time.
    """
    def __init__(self, value, time=0):
        self.value = value
        self.time = time

    def __eq__(self, token):
        return self.value == token.value and self.time == token.time

    def __lt__(self, token):
        return (self.value, self.time) < (token.value, token.time)

    def __hash__(self):
        return (self.value, self.time).__hash__()

    def __str__(self):
        result = str(self.value)
        if self.time is not None:
            result += "@" + str(self.time)
        return result

    def __repr__(self):
        return self.__str__()


class SimProblem:
    """
    A simulation problem SimProblem, which consists of a collection of simulation variables SimVar and a collection of simulation events SimEvent.
    The simulation has a time and a marking of SimVar. A marking is an assignment of values to SimVar variables (also see SimVar).
    The difference between a normal Python variable and a SimVar is that: (1) a SimVar can have multiple values; and (2) these values have a simulation time
    at which they become available. A SimEvent is a function that takes SimVar values as input and produces SimVar values (also see SimEvent). The difference with normal
    Python functions is that events can happen whenever its incoming SimVar parameters have a value. If a SimVar parameter has multiple values,
    it can happen on any of these values.

    :param debugging: if set to True, produces more information for debugging purposes (defaults to True).
    """
    def __init__(self, debugging=True):
        self.places = []
        self.events = []
        self.id2node = dict()
        self.clock = 0
        self._debugging = debugging

    def __str__(self):
        result = ""
        result += "P={"
        for i in range(len(self.places)):
            result += str(self.places[i])
            if i < len(self.places) - 1:
                result += ","
        result += "}\n"
        result += "T={"
        for i in range(len(self.events)):
            result += str(self.events[i])
            if self.events[i].guard is not None:
                result += "[" + self.events[i].guard.__name__ + "]"
            result += ":" + self.events[i].behavior.__name__
            if i < len(self.events) - 1:
                result += ","
        result += "}\n"
        arcs = []
        for t in self.events:
            for p in t.incoming:
                arcs.append("(" + str(p) + "," + str(t) + ")")
            for p in t.incoming:
                arcs.append("(" + str(t) + "," + str(p) + ")")
        result += "A={"
        for i in range(len(arcs)):
            result += arcs[i]
            if i < len(arcs) - 1:
                result += ","
        result += "}\n"
        markings = []
        for p in self.places:
            if len(p.marking_order) > 0:
                mstr = str(p) + ":"
                ti = 0
                for token in p.marking_order:
                    mstr += str(p.marking_count[token]) + "`" + str(token) + "`"
                    if ti < len(p.marking_order) - 1:
                        mstr += "++"
                    ti += 1
                markings.append(mstr)
        result += "M={"
        for i in range(len(markings)):
            result += markings[i]
            if i < len(markings) - 1:
                result += ","
        result += "}"                
        return result

    def add_var(self, name):
        """
        Creates a new SimVar with the specified name as identifier. Adds the SimVar to the problem and returns it.

        :param name: a name for the SimVar.
        :return: a SimVar with the specified name as identifier.
        """
        # Check name
        if name in self.id2node:
            raise TypeError("Node with name " + name + " already exists. Names must be unique.")

        # Generate and add SimVar
        result = SimVar(name)
        self.places.append(result)
        self.id2node[name] = result

        return result

    def var(self, name):
        """
        Returns the SimVar with the given name.
        Raises an error if no such SimVar exists.

        :param name: the name of the SimVar.
        :return: the SimVar with the given name or an Error.
        """
        if name in self.id2node:
            if isinstance(self.id2node[name], SimVar):
                return self.id2node[name]
            else:
                raise TypeError(name + " is not a SimVar.")
        else:
            raise LookupError("SimVar " + name + ": does not exist.")

    def add_event(self, inflow, outflow, behavior, name=None, guard=None):
        """
        Creates a new SimEvent with the specified parameters (also see SimEvent). Adds the SimEvent to the problem and returns it.

        :param inflow: a list of incoming SimVar of the event.
        :param outflow: a list of outgoing SimVar of the event/
        :param behavior: a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many elements as there are outgoing SimVar. When the event happens, the function is performed on the incoming SimVar and the result of the function is put on the outgoing SimVar.
        :param name: the identifier of the event.
        :param guard: a function that takes as many parameters as there are incoming SimVar. The function must evaluate to True or False for all possible values of SimVar. The event can only happen for values for which the guard function evaluates to True.
        :return: a SimEvent with the specified parameters.
        """

        # Check name
        t_name = name
        if t_name is None:
            if behavior.__name__ == "<lambda>":
                raise TypeError("Event name must be set or procedure behavior function must be named.")
            else:
                t_name = behavior.__name__
        if t_name in self.id2node:
            raise TypeError("Event " + t_name + ": node with the same name already exists. Names must be unique.")

        # Check inflow
        c = 0
        for i in inflow:
            if not isinstance(i, SimVar):
                raise TypeError("Event " + t_name + ": inflow with index " + str(c) + " is not a SimVar.")
            c += 1

        # Check outflow
        c = 0
        for o in outflow:
            if not isinstance(o, SimVar):
                raise TypeError("Event " + t_name + ": outflow with index " + str(o) + " is not a SimVar.")
            c += 1

        # Check behavior function
        if not callable(behavior):
            raise TypeError("Event " + t_name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        parameters = inspect.signature(behavior).parameters
        if len(parameters) != len(inflow):
            raise TypeError("Event " + t_name + ": the behavior function must take as many parameters as there are input variables.")

        # Check constraint
        if guard is not None:
            if not callable(guard):
                raise TypeError("Event " + t_name + ": the constraint must be a function. (Maybe you made it a function call, exclude the brackets.)")
            parameters = inspect.signature(guard).parameters
            if len(parameters) != len(inflow):
                raise TypeError("Event " + t_name + ": the constraint function must take as many parameters as there are input variables.")

        # Generate and add SimEvent
        result = SimEvent(t_name, guard=guard, behavior=behavior, incoming=inflow, outgoing=outflow)
        self.events.append(result)
        self.id2node[t_name] = result

        return result

    @staticmethod
    def tokens_combinations(event):
        """
        Creates a list of token combinations that are available to the specified event.
        These are combinations of tokens that are on the incoming SimVar of the event.
        For example, if a event has incoming SimVar a and b with tokens 1@0 on a and 2@0, 3@0 on b,
        the possible combinations are [(a, 1@0), (b, 2@0)] and [(a, 1@0), (b, 3@0)]

        :param event: the event to return the token combinations for.
        :return: a list of lists, each of which is a token combination.
        """
        # create all possible combinations of incoming token values
        bindings = [[]]
        for place in event.incoming:
            new_bindings = []
            for token in place.marking_order:  # get set of colors in incoming place
                for binding in bindings:
                    new_binding = binding.copy()
                    new_binding.append((place, token))
                    new_bindings.append(new_binding)
            bindings = new_bindings
        return bindings

    def event_bindings(self, event):
        """
        Calculates the set of bindings that enables the given event.
        Each binding is a tuple ([(place, token), (place, token), ...], time) that represents a single enabling binding.
        A binding is
        a possible token combination (see token_combinations), for which the event's
        guard function evaluates to True. In case there is no guard function, any combination is also a binding.
        The time is the time at which the latest token is available.
        For example, if a event has incoming SimVar a and b with tokens 1@2 on a and 2@3, 3@1 on b,
        the possible bindings are ([(a, 1@2), (b, 2@3)], 3) and ([(a, 1@2), (b, 3@1)], 2)

        :param event: the event for which to calculate the enabling bindings.
        :return: list of tuples ([(place, token), (place, token), ...], time)
        """
        if len(event.incoming) == 0:
            raise Exception("Though it is strictly speaking possible, we do not allow events like '" + str(self) + "' without incoming arcs.")

        bindings = self.tokens_combinations(event)

        # a binding must have all incoming places
        nr_incoming_places = len(event.incoming)
        new_bindings = []
        for binding in bindings:
            if len(binding) == nr_incoming_places:
                new_bindings.append(binding)
        bindings = new_bindings

        # if a event has a guard, only bindings are enabled for which the guard evaluates to True
        result = []
        for binding in bindings:
            variable_values = []
            time = None
            for (place, token) in binding:
                variable_values.append(token.value)
                if time is None or token.time > time:
                    time = token.time
            enabled = True
            if event.guard is not None:
                try:
                    enabled = event.guard(*variable_values)
                except Exception as e:
                    raise TypeError("Event " + event + ": guard generates exception for values " + str(variable_values) + ".") from e
                if self._debugging and not isinstance(enabled, bool):
                    raise TypeError("Event " + event + ": guard does evaluate to a Boolean for values " + str(variable_values) + ".")
            if enabled:
                result.append((binding, time))
        return result

    def bindings(self):
        """
        Calculates the set of timed bindings that is enabled over all events in the problem.
        Each binding is a tuple ([(place, token), (place, token), ...], time, event) that represents a single enabling binding.
        If no timed binding is enabled at the current clock time, updates the current clock time to the earliest time at which there is.
        :return: list of tuples ([(place, token), (place, token), ...], time, event)
        """
        untimed_bindings = []
        timed_bindings = []
        for t in self.events:
            for (binding, time) in self.event_bindings(t):
                if time is None:
                    untimed_bindings.append((binding, time, t))
                else:
                    timed_bindings.append((binding, time, t))
        # timed bindings are only enabled if they have time <= clock
        # if there are no such bindings, set the clock to the earliest time at which there are
        timed_bindings.sort(key=lambda b: b[1])
        if len(timed_bindings) > 0 and timed_bindings[0][1] > self.clock:
            self.clock = timed_bindings[0][1]
        # now return the untimed bindings + the timed bindings that have time <= clock
        return untimed_bindings + [(binding, time, t) for (binding, time, t) in timed_bindings if time <= self.clock]

    def fire(self, timed_binding):
        """
        Fires the specified timed binding.
        Binding is a tuple ([(place, token), (place, token), ...], time, event)
        """
        (binding, time, event) = timed_binding

        # process incoming places:
        variable_assignment = []
        for (place, token) in binding:
            # remove tokens from incoming places
            place.remove_token(token)
            # assign values to the variables on the arcs
            variable_assignment.append(token.value)

        # calculate the result of the behavior of the event
        try:
            result = event.behavior(*variable_assignment)
        except Exception as e:
            raise TypeError("Event " + str(event) + ": behavior function generates exception for values " + str(variable_assignment) + ".") from e
        if self._debugging:
            if type(result) != list:
                raise TypeError("Event " + str(event) + ": behavior function does not generate a list for values " + str(variable_assignment) + ".")
            if len(result) != len(event.outgoing):
                raise TypeError("Event " + str(event) + ": behavior function does not generate as many values as there are output variables for values " + str(variable_assignment) + ".")
            i = 0
            for r in result:
                if not isinstance(r, SimToken):
                    raise TypeError("Event " + str(event) + ": does not generate a token for variable " + str(event.outgoing[i]) + " for values " + str(variable_assignment) + ".")
                if not (type(r.time) is int or type(r.time) is float):
                    raise TypeError("Event " + str(event) + ": does not generate a numeric value for the delay of variable " + str(event.outgoing[i]) + " for values " + str(variable_assignment) + ".")
                i += 1

        for i in range(len(result)):
            token = SimToken(result[i].value, time=self.clock + result[i].time)
            event.outgoing[i].add_token(token)

    def simulate(self, duration, reporter=None):
        """
        Executes a simulation run for the problem for the specified duration.
        A simulation run executes events until this is no longer possible, or until the specified duration.
        If at any moment multiple events can happen, one is selected at random.
        At the end of the simulation run, the problem is in the state that is the result of the run.
        If the reporter is set, its callback function is called with parameters (binding, time, event)
        each time a event happens (for a binding at a moment in simulation time).

        :param duration: the duration of the simulation.
        :param reporter: a class that implements a callback function, which is called each time a event happens.
        """
        active_model = True
        while self.clock <= duration and active_model:
            bindings = self.bindings()
            if len(bindings) > 0:
                timed_binding = bindings[0]
                self.fire(timed_binding)
                if reporter is not None:
                    reporter.callback(timed_binding)
            else:
                active_model = False


def event(sim_problem: SimProblem, inflow: list, outflow: list, guard=None):
    """
    A decorator that can be used to turn a Python function into a SimEvent.
    The event will be added to the specified sim_problem.
    If they do not yet exist, SimVar will be added for each parameter of the Python function and for each element in outflow.
    The parameters of the function will be treated as inflow variables of the SimEvent (by name).
    The elements of outflow must be names of SimVar and will be treated as outflow variables of the SimEvent (by name).
    The name of the SimEvent will be the name of the Python function.

    :param sim_problem: the SimProblem to which to add the SimEvent.
    :param inflow: a list of names of inflow variables. Just there for documentation purposes, it is not being used.
    :param outflow: a list of names of outflow variables.
    :param guard: an optional guard for the SimEvent.
    :return: the Python function.
    """
    def decorator_event(func):
        parameters = inspect.signature(func).parameters
        for parameter in list(parameters.keys()) + outflow:
            if parameter not in sim_problem.id2node:
                sim_problem.add_var(parameter)
        inflow_svars = [sim_problem.id2node[parameter] for parameter in parameters]
        outflow_svars = [sim_problem.id2node[parameter] for parameter in outflow]
        sim_problem.add_event(inflow_svars, outflow_svars, func, guard=guard)
        return func
    return decorator_event
