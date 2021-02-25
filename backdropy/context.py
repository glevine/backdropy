from collections import UserDict
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
from threading import local

# The current context is synchronized to thread-local storage.
Vars = local()


class Context(UserDict):
    """
    The context stack is made up of contexts derived from other contexts. A
    single context contains its own information, as well as the information from
    all contexts that came before it.
    """

    def __init__(self, parent, *args, **kwargs):
        if parent is not None:
            data = deepcopy(parent.data)
            kwargs = {**data, **kwargs}

        super().__init__(*args, **kwargs)
        self.parent = parent

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        setattr(Vars, key, value)

    def __delitem__(self, key):
        """
        Deleting variables is not supported.

        Derive a child context using push (or the scope context manager) to add
        temporary context that can be removed using pop.
        """
        pass


# The context at the top of the stack.
Current = Context(None)


def push(**kwargs) -> Context:
    """
    Create a child context.
    """
    global Current
    Current = Context(Current, kwargs)
    return Current


def pop():
    """
    Remove the current context, thus restoring its parent context.
    """
    global Current

    def rebuild_vars(ctx: Context):
        Vars.__dict__.clear()
        for key, value in vars(ctx.data):
            setattr(Vars, key, value)

    if Current.parent is not None:
        Current = Current.parent
        rebuild_vars(Current)


def add(**kwargs):
    """
    Adds information to the current context.
    """
    Current.update(kwargs)


def contextual(fn, **vars):
    """
    A decorator that creates a new child context for the callable and removes it
    automatically.
    """

    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            push(**vars)
            return fn(*args, **kwargs)
        finally:
            pop()

    return decorator


@contextmanager
def scope(**vars):
    """
    A context manager that creates a new child context and removes it
    automatically.

    with scope(answer=42) as ctx:
        answer = Answers.load(answer=42)
        ctx.update(name=answer.name, source=answer.source)
        logger.info('generate question') # [answer=42][name=Ultimate Question][source=Deep Thought] generate question
        with scope(task='generate_question') as inner_ctx:
            earth = SuperComputers.create(name='Earth')
            inner_ctx['source'] = earth.name
            question = earth.produce(answer.answer)
            logger.info(f'question: {question}') # [answer=42][name=Ultimate Question][source=Earth] question: ???
        logger.info('question generated') # [answer=42][name=Ultimate Question][source=Deep Thought] question generated
    """

    try:
        ctx = push(**vars)
        yield ctx
    finally:
        pop()
