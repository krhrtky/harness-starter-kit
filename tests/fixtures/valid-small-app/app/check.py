from orders import cancel

assert cancel('pending') == 'cancelled'
assert cancel('cancelled') == 'cancelled'
try:
    cancel('shipped')
except ValueError:
    pass
else:
    raise AssertionError('shipped order was cancelled')
