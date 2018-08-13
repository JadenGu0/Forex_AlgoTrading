class EquityError(Exception):
    def __init__(self, err="Equity Not Enough"):
        Exception.__init__(self, err)
