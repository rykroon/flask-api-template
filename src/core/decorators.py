#from functools import update_wrapper, wraps

# Examples of function based decorators

# def my_decorator(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         #before
#         return func(*args, **kwargs)
#     return wrapper


# def my_decorator_factory(x, y):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             #before
#             return func(x, y, *args, **kwargs)
#         return wrapper
#     return decorator
