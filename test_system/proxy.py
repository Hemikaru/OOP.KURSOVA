class TestProxy:
    def __init__(self, user):
        self.user = user

    def can_edit(self) -> bool:
        return self.user is not None and self.user.role == "admin"

    def can_pass(self) -> bool:
        return self.user is not None and self.user.role == "student"