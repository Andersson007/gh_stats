#!/usr/bin/python3

from abc import (
    ABC,
    abstractmethod,
)


class Handler(ABC):

    @abstractmethod
    def get_id(self):
        pass

    @abstractmethod
    def add(self):
        pass
