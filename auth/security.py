import os
from argon2 import PasswordHasher
JWT_SECRET = os.environ.get("secret")
ph = PasswordHasher(time_cost = 3, memory_cost = 65536, parallelism = 4)