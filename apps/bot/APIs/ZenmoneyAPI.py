from zenmoney import Request, OAuth2, Diff

from petrovich.settings import env


class ZenmoneyAPI:
    def __init__(self):
        self.oauth = OAuth2(env.str("ZENMONEY_CONSUMER_KEY"), env.str("ZENMONEY_CONSUMER_SECRET"),
                            env.str("ZENMONEY_USER"), env.str("ZENMONEY_PASSWORD"))
        self.api = Request(self.oauth.token)

        self.diff = None

    def _get_diff(self):
        if not self.diff:
            self.diff = self.api.diff(Diff(**{'serverTimestamp': 1}))
        return self.diff

    def _get_debt_account(self):
        diff = self._get_diff()
        for account in diff.account:
            if account.title == 'Debt':
                return account.id
        else:
            raise RuntimeError("Не найден счет Debt")

    def _get_transactions(self):
        return self._get_diff().transaction

    def _get_merchant_id_by_name(self, name):
        for merchant in self._get_diff().merchant:
            if merchant.title == name:
                return merchant.id
        raise RuntimeError("Не найден мерчант")

    def _get_transactions_by_user_name(self, name):
        user_id = self._get_merchant_id_by_name(name)
        transactions = self._get_transactions()
        return list(
            sorted(filter(lambda x: x.merchant == user_id and not x.deleted, transactions), key=lambda x: x.created)
        )

    def _calculate_debt(self, transactions):
        debt_account = self._get_debt_account()

        # outcome_transactions = []
        # income_transactions = []
        outcome_sum = 0
        income_sum = 0
        for transaction in transactions:
            if transaction.incomeAccount == debt_account:
                # outcome_transactions.append(transaction)
                outcome_sum += transaction.income
            elif transaction.outcomeAccount == debt_account:
                # income_transactions.append(transaction)
                income_sum += transaction.income
        debt = outcome_sum - income_sum
        return debt

    def get_last_transactions_for_debt_by_name(self, name):
        transactions_by_user = self._get_transactions_by_user_name(name)
        debt_account = self._get_debt_account()

        debt = self._calculate_debt(transactions_by_user)

        delta = debt
        transactions = []
        delta_exact_zero = False
        if delta > 0:
            for transaction in reversed(transactions_by_user):
                if transaction.incomeAccount == debt_account:
                    delta -= transaction.outcome
                    transactions.append(transaction)
                elif transaction.outcomeAccount == debt_account:
                    delta += transaction.income
                    transactions.append(transaction)
                if delta <= 0:
                    if delta == 0:
                        delta_exact_zero = True
                    break
        transactions_dict = [
            {'created': x.created,
             'comment': x.comment,
             'amount': x.outcome,
             'incoming': x.incomeAccount == debt_account
             } for x in transactions]
        return {'transactions': reversed(transactions_dict), 'debt': debt, 'delta_exact_zero': delta_exact_zero}