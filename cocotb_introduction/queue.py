"""
Contains the basic definition of queue built with the cocotb.triggers.Event.
Queue is used to safely move data between tasks.

WARNING: As it turns out, cocotb already comes with a Queue!
         Didn't realize it at the time, so use cocotb's version instead.
"""
import collections
import typing
import cocotb.triggers as triggers


T = typing.TypeVar("T")


class QueueEmpty(BaseException):
    pass


class Queue(typing.Generic[T]):
    """Basic queue for safely moving messages between tasks."""

    def __init__(self) -> None:
        super().__init__()
        self._deque: typing.Deque[T] = collections.deque()
        self._event = triggers.Event()

    @property
    def empty(self) -> bool:
        """Indicates the queue empty."""
        return not self._deque

    @property
    def event(self) -> triggers.PythonTrigger:
        """Current task resumes when change occurs on the queue, so if there's a push or a pop."""
        self._event.clear()
        return self._event.wait()

    def push(self, value: T):
        """Pushes data into the queue."""
        self._event.set()
        self._deque.append(value)

    def pop(self) -> T:
        """Reads data from the queue."""
        if self.empty:
            raise QueueEmpty()
        self._event.set()
        return self._deque.popleft()

    def peek(self) -> T:
        """Peeks data from the queue."""
        if self.empty:
            raise QueueEmpty()
        return self._deque[0]

    async def pop_wait(self) -> T:
        """Current task resumes when data is available in the queue, then data is read from the queue."""
        while self.empty:
            await self.event
        return self.pop()

