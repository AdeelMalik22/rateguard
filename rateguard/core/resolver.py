class KeyResolver:

    def __init__(self, func=None):
        self.func = func


    def resolve(self, *args, **kwargs):

        if self.func:
            return self.func(*args, **kwargs)


        request = None


        for arg in args:
            if hasattr(arg, "client"):
                request = arg
                break


        for value in kwargs.values():
            if hasattr(value, "client"):
                request = value
                break


        if request is None:
            return "anonymous"


        # check if authentication middleware exists
        if "user" in request.scope:

            user = request.scope["user"]

            if hasattr(user, "id"):
                return f"user:{user.id}"


        # fallback
        return f"ip:{request.client.host}"