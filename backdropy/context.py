from contextlib import contextmanager
from functools import wraps
from threading import local


class ThreadContext(local):
    """
    All context is managed through thread-local data. There is always one active
    context per thread but additional contexts may be derived from the active
    context. When a child context is created it becomes the active context.

    The active context contains its own information, as well as the information
    from all contexts that came before it. Use `Context.data` to access the
    context instead of `vars(Context)` or `Context.__dict__`.

    Deleting data is not supported. Create a child context using
    `Context.push()` (or `scope()`) to add temporary context that can be removed
    using `Context.pop()`.
    """

    def push(self, **kwargs):
        """
        Create a child context.
        """

        # Add a new context to the stack. The parent context's values are
        # preserved beneath the child context. The None's will be removed from
        # the stack when the context is removed, revealing the parent context's
        # data untouched.
        for value in vars(self).values():
            value.append(None)

        # Set the values for the new context.
        self.add(**kwargs)

    def pop(self):
        """
        Remove the current context, thus restoring its parent context.
        """

        # Remove the current context from the stack.
        for key, value in vars(self).items():
            try:
                value.pop()
            except IndexError:
                pass
            finally:
                # There is no need for this attribute anymore.
                if len(value) == 0:
                    delattr(self, key)

    def add(self, **kwargs):
        """
        Add information to the current context. Data is overwritten when key
        collisions occur.
        """

        for key, value in kwargs.items():
            attr = getattr(self, key, [])
            attr.append(value)
            setattr(self, key, attr)

    @property
    def data(self) -> dict:
        """
        Return all information from the current context.
        """

        data = {}

        for key, value in vars(self).items():
            compressed = [v for v in value if v]

            if len(compressed) > 0:
                data[key] = compressed[-1]

        return data


# Initialize the context.
Context = ThreadContext()


def contextual(fn, **vars):
    """
    A decorator that creates a new child context for the callable and removes it
    automatically.
    """

    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            Context.push(**vars)
            return fn(*args, **kwargs)
        finally:
            Context.pop()

    return decorator


@contextmanager
def scope(**vars):
    """
    A context manager that creates a new child context and removes it
    automatically.

    with scope(answer=42) as ctx:
        answer = Answers.load(answer=42)
        ctx.add(name=answer.name, source=answer.source)
        logger.info('generate question') # [answer=42][name=Ultimate Question][source=Deep Thought] generate question
        with scope(task='generate_question') as inner_ctx:
            earth = SuperComputers.create(name='Earth')
            inner_ctx.add(source=earth.name)
            question = earth.produce(answer.answer)
            logger.info(f'question: {question}') # [answer=42][name=Ultimate Question][source=Earth] question: ???
        logger.info('question generated') # [answer=42][name=Ultimate Question][source=Deep Thought] question generated
    """

    try:
        Context.push(**vars)
        yield Context
    finally:
        Context.pop()
