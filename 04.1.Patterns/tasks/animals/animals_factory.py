import abc
import typing as tp

from animals import Cat, Cow, Dog


class Animal(abc.ABC):
    @abc.abstractmethod
    def say(self) -> str:
        pass


class CatAdapter(Animal):
    def __init__(self, cat: Cat) -> None:
        self._cat = cat

    def say(self) -> str:
        return self._cat.say()


class DogAdapter(Animal):
    def __init__(self, dog: Dog) -> None:
        self._dog = dog

    def say(self) -> str:
        return self._dog.say("woof")


class CowAdapter(Animal):
    def __init__(self, cow: Cow) -> None:
        self._cow = cow

    def say(self) -> str:
        return self._cow.talk()


def animals_factory(animal: tp.Any) -> Animal:
    if isinstance(animal, Cat):
        return CatAdapter(animal)
    if isinstance(animal, Dog):
        return DogAdapter(animal)
    if isinstance(animal, Cow):
        return CowAdapter(animal)
    raise TypeError(f"Unknown animal type: {type(animal)}")
