def get_or_default(target, default_val):
    return default_val if target == None else target

def assert_str(target):
    assert isinstance(target, str)

def create_generator(values):
    results = collections.deque([None, True, True, None])
    return lambda: results.popleft()
