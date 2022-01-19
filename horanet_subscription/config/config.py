SUBSCRIPTION_STATE = [('draft', 'New'),
                      ('pending', 'Pending'),
                      ('active', 'Active'),
                      ('to_compute', 'Need computation'),
                      ('closed', 'closed'),
                      ('done', 'Done')]
SUBSCRIPTION_LINE_STATE = SUBSCRIPTION_STATE + [('invoiced', 'Invoiced')]

PACKAGE_STATE = SUBSCRIPTION_STATE
PACKAGE_LINE_STATE = SUBSCRIPTION_LINE_STATE

ACTION_MODE = [('query', "Query"), ('operation', "Operation")]
