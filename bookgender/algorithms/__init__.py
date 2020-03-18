explicit_algos = ['user-user', 'item-item', 'als']
implicit_algos = ['user-user', 'item-item', 'wrls', 'bpr']

data_algos = {
    'BX-E': explicit_algos,
    'BX-I': implicit_algos,
    'AZ': explicit_algos + [f'{a}-imp' for a in implicit_algos],
    'GR-E': [a for a in explicit_algos if a != 'als'],
    'GR-I': implicit_algos
}
