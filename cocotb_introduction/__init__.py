import collections
import typing
import cocotb.triggers as triggers
import cocotb.handle as handle


T = typing.TypeVar("T")


class QueueEmpty(BaseException):
    pass


class Queue(typing.Generic[T]):
    def __init__(self) -> None:
        super().__init__()
        self._deque: typing.Deque[T] = collections.deque()
        self._event = triggers.Event()

    @property
    def empty(self) -> bool:
        return not self._deque

    @property
    def event(self) -> triggers.PythonTrigger:
        self._event.clear()
        return self._event.wait()

    def push(self, value: T):
        self._event.set()
        self._deque.append(value)

    def pop(self) -> T:
        if self.empty:
            raise QueueEmpty()
        self._event.set()
        return self._deque.popleft()

    async def popwait(self) -> T:
        while self.empty:
            await self.event
        return self.pop()


async def reset(clk: handle.SimHandleBase, rst: handle.SimHandleBase, cycles: int=4) -> None:
    rst.value = 1
    for _ in range(cycles):
        await triggers.RisingEdge(clk)
    rst.value = 0