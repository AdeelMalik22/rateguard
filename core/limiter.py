

class RateLimiter:

    def __init__(
        self,
        algorithm
    ):
        self.algorithm = algorithm


    def check(self, client_id):

        return self.algorithm.allow(
            client_id
        )