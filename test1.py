class Animal:
    def __init__(self, name, species):
        self.name = name
        self.species = species

    def make_sound(self):
        print(f"{self.name} the {self.species} makes a sound!")

dog = Animal("Buddy", "Dog")
dog.make_sound()
