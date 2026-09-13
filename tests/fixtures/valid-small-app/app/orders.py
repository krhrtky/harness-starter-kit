def cancel(state):
    if state == 'shipped':
        raise ValueError('shipped orders cannot be cancelled')
    return 'cancelled'
