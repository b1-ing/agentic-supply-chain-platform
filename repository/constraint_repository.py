class ConstraintRepository:
    def __init__(self):

        self.constraints = []

    def add(self, constraint):

        self.constraints.append(constraint)

    def add_many(self, constraints):

        self.constraints.extend(constraints)

    def get_all(self):

        return self.constraints

    def clear(self):

        self.constraints.clear()
